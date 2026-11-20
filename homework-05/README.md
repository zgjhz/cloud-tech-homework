# ДЗ 5 — RabbitMQ, маршрутизация и DLQ

Три сервиса Docker Compose: RabbitMQ 4.4.1 management, Python producer и consumer.
Python 3.13.9 и pika 1.3.2 устанавливаются внутри образа; дополнительное ПО на Mac
не требуется. Для проверочного скрипта используется установленный Python 3.

## Запуск

Из каталога `homework-05/`:

```sh
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
cp .env.example .env
# При повторном запуске сохраняйте существующий .env.
docker compose config --quiet
docker compose up -d --build --wait
docker compose ps
docker compose logs --tail=20 producer consumer
```

Management UI: http://127.0.0.1:15672, логин/пароль из `.env`
(учебный пример: `homework` / `local-homework-only`). AMQP-порт наружу не публикуется;
клиенты обращаются к `rabbitmq:5672` внутри Compose-сети. `.env` исключён из Git.
При занятом management-порте задайте `MANAGEMENT_PORT=15674` перед командой запуска.

## Маршруты и сообщения

Direct exchange `operations` направляет ключ `add` в `operations.add`,
`multiply` в `operations.multiply`, `divide` в `operations.divide`.
Producer каждые 5 секунд отправляет очередную операцию с аргументами `[12,3]`.
Сообщение содержит `id`, `operation`, `args`; AMQP correlation_id совпадает с id.
Publisher confirms и mandatory проверяют принятие/маршрутизацию публикации.

Consumer обслуживает все три очереди, выводит JSON в stdout и подтверждает
успешное сообщение после записи результата. Результаты: 15, 36 и 4.
При неверном payload, неизвестной операции или делении на ноль он печатает
ошибку и выполняет `basic_nack(requeue=False)`. Политика `operations-dlx`
направляет сообщение через `operations.dlx` с ключом `failed` в `operations.dlq`.
DLQ не включена в рабочую политику, что исключает цикл dead lettering.

Очереди/exchanges durable, сообщения persistent, данные RabbitMQ в именованном
томе со стабильным hostname. Это односерверная учебная установка, без обещания
exactly-once: при сбое между логированием и ack результат может повториться.

## Проверка конфигурации и периодической отправки

```sh
docker compose exec rabbitmq rabbitmqctl list_bindings source_name destination_name routing_key
docker compose exec rabbitmq rabbitmqctl list_policies
docker compose exec rabbitmq rabbitmqctl list_queues name messages_ready messages_unacknowledged
docker compose logs --tail=20 producer consumer
```

Ограниченная отправка (три задания, по одному на операцию):

```sh
docker compose stop producer
docker compose run --rm --no-deps producer python -m app.producer --count 3 --interval 0
docker compose start producer
```

## Автоматические проверки

Unit-тесты вычислений, деления на ноль и неверного payload:

```sh
docker compose run --rm --no-deps consumer python -m unittest discover -s tests -v
```

Полная проверка маршрутизации и DLQ:

```sh
python3 scripts/verify.py
```

Скрипт создаёт отдельный Compose-проект `hw05-test-<случайный id>` с отдельным
томом и management-портом 15673 (порт должен быть свободен). До запуска consumer
проверяет попадание каждого задания в правильную очередь и свойства persistent.
Затем запускает настоящий consumer, отправляет деление на ноль и неверный payload,
проверяет исходные id в DLQ, `x-death.reason=rejected`, `count=1`, пустые рабочие
очереди и журнал четырёх успешных вычислений, включая задание после ошибки.
На выходе `PASS`; ошибка приводит к ненулевому коду выхода. В finally удаляются
только временные контейнеры и том этого теста. Основная лабораторная не очищается.
Не запускайте две проверки одновременно из-за общего тестового порта.

Чтобы оставить ошибки в основной DLQ для просмотра в UI:

```sh
docker compose run --rm --no-deps producer python -c 'from app.common import connect; from app.producer import publish; from uuid import uuid4; c=connect(); ch=c.channel(); ch.confirm_delivery(); publish(ch,{"id":str(uuid4()),"operation":"divide","args":[1,0]},"divide"); c.close()'
docker compose logs --tail=10 consumer
```

В UI откройте Queues → operations.dlq → Get messages, выбрав requeue, чтобы
просмотреть сообщение без удаления. Прямой publish с несуществующим routing key
отклоняется producer как unroutable; это не вычислительная ошибка consumer.

## Остановка и очистка

`docker compose down` сохраняет том и очереди. `docker compose up -d --wait`
возобновляет работу. `docker compose down -v` **удаляет все данные этой лабораторной**.
Смена `.env` не меняет учётные данные уже инициализированного брокера: используйте
прежние параметры или явно выполните полный сброс. При обновлении topology
изменения в `rabbitmq/definitions.json` применяются после пересборки и пересоздания брокера: `docker compose up -d --build`.

## Результаты — 21 ноября 2026

Проверено на macOS ARM64, Docker Engine 29.9.3, Compose 5.7.0.
RabbitMQ `4.4.1-management-alpine` имеет manifest digest
`sha256:2b47b1aa05ec7e373950ad2e9200e9f95a9da7039c8d22c19dbf5a59101362c4`.

- Три сервиса запущены; bindings и DLX policy подтверждены `rabbitmqctl`.
- Unit-тесты: 3 passed (операции и невалидные данные проверяются подслучаями).
- Периодический producer и режим `--count 3 --interval 0` работают.
- На новом пустом тестовом томе: PASS route add/multiply/divide.
- Два ошибочных сообщения оказались в DLQ с исходными id, причиной rejected
  и счётчиком x-death=1; рабочие очереди опустели.
- Журнал содержит результаты 15, 36, 4 и успешное вычисление 5 после ошибки.
- Временный проект и только его тестовый том удалены после проверки.

Конфигурация входит в образ RabbitMQ, а не монтируется с macOS. Стартовый скрипт
работает от пользователя rabbitmq, ждёт готовности сервера и импортирует topology
после создания vhost/пользователя. Healthcheck учитывает завершение импорта.
