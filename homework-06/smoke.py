"""Verify the downloaded Registry image through its published HTTP port."""

import json
import urllib.error
import urllib.request
from uuid import uuid4


def request(path, body=None):
    req = urllib.request.Request(
        "http://127.0.0.1:8086" + path,
        data=None if body is None else json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        return response.status, json.load(response)


def main():
    assert request("/health") == (200, {"status": "ok"})
    name = f"registry-smoke-{uuid4()} O'Reilly"
    status, item = request("/items", {"name": name})
    assert status == 201 and isinstance(item["id"], int) and item["name"] == name
    status, items = request("/items")
    assert status == 200 and item in items
    try:
        request("/items", {"name": ""})
    except urllib.error.HTTPError as exc:
        assert exc.code == 422
    else:
        raise AssertionError("Invalid input was accepted")
    print(f"PASS Registry image: health, create/read {item}, invalid input 422")


if __name__ == "__main__":
    main()
