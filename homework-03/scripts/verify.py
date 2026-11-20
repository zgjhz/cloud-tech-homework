#!/usr/bin/env python3
"""Verify host access, replica routing and optional pod replacement."""
import argparse
import json
import subprocess
import time
import urllib.request

KUBECTL = ["kubectl", "--context", "cloud-homework", "-n", "homework-03"]


def kubectl(*args):
    return subprocess.check_output(KUBECTL + list(args), text=True)


def ready_pods():
    pods = json.loads(kubectl("get", "pods", "-l", "app=backend", "-o", "json"))
    return {p["metadata"]["name"] for p in pods["items"]
            if not p["metadata"].get("deletionTimestamp") and any(
                c["type"] == "Ready" and c["status"] == "True"
                for c in p.get("status", {}).get("conditions", []))}


def check_routing(url, expected):
    seen = set()
    for _ in range(100):
        req = urllib.request.Request(url + "/demo?source=host", headers={"Connection": "close"})
        with urllib.request.urlopen(req, timeout=5) as response:
            assert response.status == 200
            assert response.headers.get("X-Lab-Frontend") == "nginx"
            data = json.load(response)
        assert data["message"] == "Hello from backend", data
        assert data["path"] == "/demo?source=host", data
        assert data["pod"] in expected, data
        seen.add(data["pod"])
        if seen == expected:
            print("PASS external frontend routes to both pods:", sorted(seen), flush=True)
            return
    raise RuntimeError(f"Expected {expected}, observed {seen} in 100 requests")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replace-pod", action="store_true")
    args = parser.parse_args()
    svc = json.loads(kubectl("get", "service", "frontend", "-o", "json"))
    assert svc["spec"]["type"] == "LoadBalancer"
    ingress = svc.get("status", {}).get("loadBalancer", {}).get("ingress", [])
    if not ingress or not ingress[0].get("ip"):
        raise RuntimeError("Start minikube tunnel -p cloud-homework in another terminal")
    ip = ingress[0]["ip"]
    url = f"http://{ip}:{svc['spec']['ports'][0]['port']}"
    backend = json.loads(kubectl("get", "service", "backend", "-o", "json"))
    assert backend["spec"]["type"] == "ClusterIP"
    pods = ready_pods()
    assert len(pods) == 2, pods
    print("Frontend URL:", url, flush=True)
    check_routing(url, pods)
    if args.replace_pod:
        victim = sorted(pods)[0]
        print(kubectl("delete", "pod", victim, "--wait=true", "--timeout=60s"), flush=True)
        for _ in range(60):
            replacement = ready_pods()
            if len(replacement) == 2 and victim not in replacement:
                break
            time.sleep(2)
        else:
            raise RuntimeError("Deployment did not restore two Ready replicas")
        print("PASS replacement:", victim, "->", sorted(replacement - pods), flush=True)
        check_routing(url, replacement)


if __name__ == "__main__":
    main()
