#!/bin/sh
set -eu
rm -f /tmp/topology-ready
docker-entrypoint.sh rabbitmq-server &
server_pid=$!
trap 'kill -TERM "$server_pid"; wait "$server_pid"' TERM INT
attempt=0
until rabbitmq-diagnostics -q check_running >/dev/null 2>&1; do
    kill -0 "$server_pid"
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 30 ]; then exit 1; fi
    sleep 2
done
rabbitmqctl import_definitions /etc/rabbitmq/definitions.json
touch /tmp/topology-ready
wait "$server_pid"
