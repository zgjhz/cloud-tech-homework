#!/usr/bin/env python3
"""Use an isolated Compose project and port for repeatable integration checks."""
import json
import os
from pathlib import Path
import subprocess
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
PREFIX='verify-'+str(uuid4())
PROJECT='hw05-test-'+uuid4().hex[:8]
ENV=dict(os.environ, MANAGEMENT_PORT='15673')
CMD=['docker','compose','-p',PROJECT]


def compose(*args):
    return subprocess.check_output(CMD+list(args),cwd=ROOT,env=ENV,text=True)


try:
    print(compose('up','-d','--build','--wait','rabbitmq'),flush=True)
    print(compose('run','--rm','--no-deps','producer','python','-m','app.verify','publish',PREFIX),flush=True)
    print(compose('up','-d','consumer'),flush=True)
    print(compose('run','--rm','--no-deps','producer','python','-m','app.verify','dlq',PREFIX),flush=True)
    logs=compose('logs','--no-log-prefix','consumer')
    results={}
    failed=set()
    for line in logs.splitlines():
        if line.startswith('{'):
            event=json.loads(line)
            if event['event']=='result': results[event['id']]=event['result']
            if event['event']=='failed': failed.add(event['id'])
    assert results == {PREFIX+'-add':15,PREFIX+'-multiply':36,PREFIX+'-divide':4,PREFIX+'-after':5}, results
    assert failed == {PREFIX+'-zero',PREFIX+'-invalid'},failed
    print('PASS result logs, errors, and successful processing after failure')
except Exception:
    print(compose("logs", "--tail=60"), flush=True)
    raise
finally:
    # This randomly named project contains only data created by this test.
    print(compose('down','-v'),flush=True)
