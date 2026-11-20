#!/usr/bin/env python3
"""Host-side smoke/persistence checks. Never deletes volumes."""
import argparse
import json
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
URL = "http://127.0.0.1:8082"


def compose(*args):
    return subprocess.check_output(
        ["docker", "compose", *args], cwd=ROOT, text=True
    )


def request(path, data=None):
    body = None if data is None else json.dumps(data).encode()
    req = urllib.request.Request(
        URL + path, data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=5) as response:
        return response.status, json.load(response)


def ready():
    for _ in range(60):
        try:
            if request("/health") == (200, {"status": "ok"}):
                return
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            pass
        time.sleep(1)
    raise RuntimeError("API did not become healthy within 60 attempts")


def check_record(item):
    status, items = request("/items")
    if status != 200 or item not in items:
        raise RuntimeError(f"Record lost: {item}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--persistence", action="store_true")
    args = parser.parse_args()
    ready()
    services = compose("ps", "--services", "--status", "running").split()
    if sorted(services) != ["db", "entrypoint"]:
        raise RuntimeError(f"Expected two running services, got {services}")
    status, item = request("/items", {"name": f"verify-{uuid4()}"})
    if status != 201 or not isinstance(item.get("id"), int):
        raise RuntimeError(f"Create failed: {status}, {item}")
    check_record(item)
    print(f"PASS create/read: {item}", flush=True)
    try:
        request("/items", {"name": ""})
    except urllib.error.HTTPError as exc:
        if exc.code != 422:
            raise
    else:
        raise RuntimeError("Invalid input was accepted")
    print("PASS invalid input: HTTP 422", flush=True)
    if args.persistence:
        compose("restart")
        ready()
        check_record(item)
        print("PASS same record after restart", flush=True)
        compose("down")
        compose("up", "-d", "--wait", "--wait-timeout", "120")
        ready()
        check_record(item)
        print("PASS same record after down/up (volume preserved)", flush=True)


if __name__ == "__main__":
    main()
