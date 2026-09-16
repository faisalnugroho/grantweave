"""Real Studionet deployment and deterministic + LLM smoke. Never submits Portal.
Usage: python scripts/live_smoke.py --deploy; python scripts/live_smoke.py --smoke
Resumes logged transaction hashes, never silently re-sends an uncertain write.
"""
import argparse
import base64
import hashlib
import json
import time
from pathlib import Path
import requests
from urllib.request import urlopen
from genlayer_py import create_client, create_account
from genlayer_py.chains import studionet

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "evidence/live.json"
KEY = Path.home() / ".genlayer-keys/grantweave-key.json"
RPC = "https://studio.genlayer.com/api"
SOURCE_REV = "184a498947dc32ce3be089f77d3e3542ec24cec9"
RUBRIC = "Only fund concrete public-goods deliverables that will be openly licensed and freely accessible without registration. Require a clear artifact, intended audience and delivery timeline."


def rpc(method, params):
    response = requests.post(RPC, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, timeout=45)
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise RuntimeError(data["error"])
    return data["result"]


def save(data):
    LOG.parent.mkdir(exist_ok=True)
    LOG.write_text(json.dumps(data, indent=2))


def wait(tx):
    deadline = time.monotonic() + 900
    while time.monotonic() < deadline:
        record = rpc("eth_getTransactionByHash", [tx])
        if record and record.get("status") in ("FINALIZED", "UNDETERMINED", "CANCELED"):
            return record
        time.sleep(10)
    raise TimeoutError("Transaction pending; resume by hash, do not resubmit: " + tx)


def succeeded(record):
    leaders = (record.get("consensus_data") or {}).get("leader_receipt") or []
    execution = record.get("tx_execution_result_name") or (leaders[0].get("execution_result") if leaders else None)
    return record.get("status") == "FINALIZED" and record.get("result_name") == "MAJORITY_AGREE" and execution in ("FINISHED_WITH_RETURN", "SUCCESS")


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--deploy", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if not args.deploy and not args.smoke:
        parser.error("choose --deploy or --smoke")
    KEY.parent.mkdir(exist_ok=True)
    if KEY.exists():
        account = create_account(account_private_key=json.loads(KEY.read_text())["private_key"])
    else:
        account = create_account()
        KEY.touch(mode=0o600)
        KEY.write_text(json.dumps({"address": account.address, "private_key": account.key.hex()}))
    client = create_client(chain=studionet, account=account)
    log = json.loads(LOG.read_text()) if LOG.exists() else {"network": "studionet", "rpc": RPC, "owner": account.address, "steps": {}}
    if args.deploy:
        source = (ROOT / "contracts/grantweave.py").read_text()
        if "deploy_tx" not in log:
            client.fund_account(account.address, 10**18)
            log["source_sha256"] = hashlib.sha256(source.encode()).hexdigest()
            log["deploy_tx"] = client.deploy_contract(code=source, account=client.local_account, args=[], leader_only=False)
            save(log)
            print("deploy", log["deploy_tx"], flush=True)
        receipt = wait(log["deploy_tx"])
        log["deploy_receipt"] = receipt
        save(log)
        if not succeeded(receipt):
            raise RuntimeError("Deployment execution/consensus not successful: " + json.dumps(receipt))
        address = (receipt.get("data") or {}).get("contract_address") or receipt.get("to_address")
        assert address, "no deployment address"
        log["address"] = address
        actual_code = base64.b64decode(receipt["data"]["contract_code"])
        assert hashlib.sha256(actual_code).hexdigest() == log["source_sha256"]
        assert json.loads(client.read_contract(address=address, function_name="list_rounds", args=[])) == [] or log["steps"]
        save(log)
        (ROOT / "frontend").mkdir(exist_ok=True)
        (ROOT / "frontend/deployment.json").write_text(json.dumps({"address": address, "network": "studionet", "chainId": 61999, "deployTx": log["deploy_tx"]}, indent=2))
        print("DEPLOY_VERIFIED", address, flush=True)
    if not args.smoke:
        return
    address = log["address"]

    def write(label, method, values, expected_success=True):
        step = log["steps"].get(label)
        if not step:
            tx = client.write_contract(address=address, function_name=method, args=values, account=client.local_account, leader_only=False)
            step = {"tx": tx, "method": method, "args": values}
            log["steps"][label] = step
            save(log)
            print(label, tx, flush=True)
        receipt = wait(step["tx"])
        step["receipt"] = receipt
        step["success"] = succeeded(receipt)
        save(log)
        if step["success"] != expected_success:
            raise RuntimeError("Unexpected transaction outcome at " + label + ": " + json.dumps(receipt))
        print(label, "verified", receipt.get("result_name"), receipt.get("tx_execution_result_name"), flush=True)

    def read(rid):
        return json.loads(client.read_contract(address=address, function_name="get_round", args=[rid]))

    def proposal(label, rid, file, amount, bad_hash=False):
        url = f"https://raw.githubusercontent.com/faisalnugroho/grantweave/{SOURCE_REV}/examples/{file}.md"
        with urlopen(url, timeout=30) as res:
            body = res.read()
        assert body == (ROOT / f"examples/{file}.md").read_bytes()
        digest = "0" * 64 if bad_hash else hashlib.sha256(body).hexdigest()
        write(label, "submit_proposal", [rid, file.replace("-", " "), url, digest, amount])

    for number in range(1, 4):
        rid = f"gw-distinct-{number}"
        write(rid + "-create", "create_round", [rid, "Public goods demonstration", RUBRIC, 100])
        proposal(rid + "-submit", rid, "open-map", 40)
        write(rid + "-seal", "seal_round", [rid])
        write(rid + "-evaluate", "evaluate_next", [rid])
        record = read(rid)
        log.setdefault("rounds", {})[rid] = record
        save(log)
        assert record["proposals"][0]["status"] == "RESERVED", record
        assert record["remaining"] == 60
    rid = "gw-overlap"
    write(rid + "-create", "create_round", [rid, "Duplicate allocation demonstration", RUBRIC, 60])
    for file, amount in [("open-map", 40), ("map-reworded", 40), ("accessibility", 30), ("private-course", 20), ("ambiguous", 10)]:
        proposal(rid + "-submit-" + file, rid, file, amount)
    write(rid + "-seal", "seal_round", [rid])
    for index, expected in enumerate(["RESERVED", "REJECTED", "OVER_BUDGET", "REJECTED", "INCONCLUSIVE"]):
        write(rid + "-evaluate-" + str(index), "evaluate_next", [rid])
        record = read(rid)
        log.setdefault("rounds", {})[rid] = record
        save(log)
        assert record["proposals"][index]["status"] == expected, record
        assert record["remaining"] == 20
    write(rid + "-double-eval-guard", "evaluate_next", [rid], False)
    rid = "gw-integrity"
    write(rid + "-create", "create_round", [rid, "Intentional hash mismatch demonstration", RUBRIC, 100])
    proposal(rid + "-submit", rid, "open-map", 40, bad_hash=True)
    write(rid + "-seal", "seal_round", [rid])
    write(rid + "-evaluate", "evaluate_next", [rid])
    record = read(rid)
    log.setdefault("rounds", {})[rid] = record
    save(log)
    assert record["proposals"][0]["status"] == "INCONCLUSIVE", record
    assert record["remaining"] == 100
    log["smoke_complete"] = True
    save(log)
    print("LIVE_SMOKE_PASS", flush=True)


if __name__ == "__main__":
    run()
