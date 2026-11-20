FROM rabbitmq:4.4.1-management-alpine
COPY rabbitmq.conf /etc/rabbitmq/rabbitmq.conf
COPY definitions.json /etc/rabbitmq/definitions.json
COPY --chmod=755 start.sh /usr/local/bin/lab-start
ENTRYPOINT ["lab-start"]
USER rabbitmq
