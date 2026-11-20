"""Deterministic broker checks; run with the periodic producer stopped."""
import json
import sys
import time
from app.common import connect, OPERATIONS
from app.producer import publish

PREFIX = sys.argv[2]
with connect() as connection:
    ch = connection.channel()
    ch.confirm_delivery()
    if sys.argv[1] == 'publish':
        for op in OPERATIONS:
            job = {'id': PREFIX+'-'+op, 'operation':op, 'args':[12,3]}
            publish(ch,job,op)
            method, props, body = ch.basic_get('operations.'+op, auto_ack=False)
            assert method and json.loads(body) == job, (op,body)
            assert props.delivery_mode == 2 and method.routing_key == op
            ch.basic_nack(method.delivery_tag,requeue=True)
            print('PASS route',op,flush=True)
        publish(ch,{'id':PREFIX+'-zero','operation':'divide','args':[1,0]},'divide')
        publish(ch,{'id':PREFIX+'-invalid'},'add')
        publish(ch,{'id':PREFIX+'-after','operation':'divide','args':[10,2]},'divide')
    elif sys.argv[1] == 'dlq':
        expected={PREFIX+'-zero',PREFIX+'-invalid'}
        found=set(); tags=[]
        deadline=time.monotonic()+30
        while time.monotonic()<deadline and found != expected:
            method, props, body=ch.basic_get('operations.dlq',auto_ack=False)
            if method:
                tags.append(method.delivery_tag)
                assert props.correlation_id in expected, props.correlation_id
                assert json.loads(body)['id'] == props.correlation_id
                death=props.headers['x-death'][0]
                assert death['reason']=='rejected' and death['count']==1, death
                found.add(props.correlation_id)
            else: connection.sleep(0.2)
        assert found == expected, found
        for tag in tags: ch.basic_nack(tag,requeue=True)
        connection.sleep(2)
        for op in OPERATIONS:
            assert ch.queue_declare(queue='operations.'+op,passive=True).method.message_count==0
        assert ch.queue_declare(queue='operations.dlq',passive=True).method.message_count==2
        print('PASS DLQ: two rejected messages, death count 1; working queues empty',flush=True)
