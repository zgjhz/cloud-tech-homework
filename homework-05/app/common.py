import os
import pika

OPERATIONS = ('add', 'multiply', 'divide')


def connect():
    return pika.BlockingConnection(pika.ConnectionParameters(
        host=os.environ.get('RABBITMQ_HOST', 'rabbitmq'),
        credentials=pika.PlainCredentials(os.environ['RABBITMQ_USER'], os.environ['RABBITMQ_PASSWORD']),
        connection_attempts=15, retry_delay=2, heartbeat=30, blocked_connection_timeout=30))
