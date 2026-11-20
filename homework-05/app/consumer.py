import json
from app.common import connect, OPERATIONS
from app.operations import calculate


def handle(channel, method, properties, body):
    job = None
    try:
        job = json.loads(body)
        result = calculate(job)
    except (ValueError, TypeError, KeyError, ZeroDivisionError, OverflowError, UnicodeDecodeError) as exc:
        print(json.dumps({'event':'failed','id':properties.correlation_id,
                          'error':str(exc)}), flush=True)
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    else:
        print(json.dumps({'event':'result','id':job['id'],'operation':job['operation'],
                          'result':result}), flush=True)
        channel.basic_ack(delivery_tag=method.delivery_tag)


def main():
    with connect() as connection:
        ch=connection.channel(); ch.basic_qos(prefetch_count=1)
        for op in OPERATIONS:
            ch.basic_consume(queue='operations.'+op, on_message_callback=handle, auto_ack=False)
        print('Consumer ready',flush=True)
        ch.start_consuming()


if __name__=='__main__': main()
