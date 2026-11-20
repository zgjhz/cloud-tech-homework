import math


def calculate(job):
    if not isinstance(job, dict) or not isinstance(job.get('id'), str) or not job['id']:
        raise ValueError('id is required')
    operation = job.get('operation')
    args = job.get('args')
    if not isinstance(args, list) or len(args) != 2:
        raise ValueError('args must contain two numbers')
    if any(type(x) not in (int, float) or not math.isfinite(x) for x in args):
        raise ValueError('args must be finite numbers')
    a, b = args
    if operation == 'add':
        result = a + b
    elif operation == 'multiply':
        result = a * b
    elif operation == 'divide':
        result = a / b
    else:
        raise ValueError('unknown operation')
    if not math.isfinite(result):
        raise ValueError('non-finite result')
    return result
