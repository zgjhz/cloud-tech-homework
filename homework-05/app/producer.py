import argparse
import json
from uuid import uuid4
import pika
from app.common import connect, OPERATIONS


def publish(channel, job, routing_key):
    channel.basic_publish(exchange='operations', routing_key=routing_key,
        body=json.dumps(job).encode(), mandatory=True,
        properties=pika.BasicProperties(content_type='application/json', delivery_mode=2,
                                       correlation_id=job['id']))
    print(json.dumps({'event':'published','id':job['id'],'routing_key':routing_key}), flush=True)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--count',type=int,default=0,help='0 = continuous')
    parser.add_argument('--interval',type=float,default=5)
    args=parser.parse_args()
    if args.count < 0 or args.interval < 0:
        parser.error('count and interval must be non-negative')
    with connect() as connection:
        ch=connection.channel(); ch.confirm_delivery()
        i=0
        while args.count == 0 or i < args.count:
            op=OPERATIONS[i % len(OPERATIONS)]
            publish(ch,{'id':str(uuid4()),'operation':op,'args':[12,3]},op)
            i+=1
            connection.sleep(args.interval)


if __name__=='__main__': main()
