# ДЗ 2 — Docker Compose и постоянная БД

Два сервисных контейнера:

- `entrypoint`: FastAPI, HTTP на `127.0.0.1:8082`.
- `db`: PostgreSQL в той же Compose-сети, адрес `db:5432`, без публикации порта на хост.

Именованный том `cloud-homework-02_postgres-data` хранит данные PostgreSQL 17
в `/var/lib/postgresql/data`. При первом запуске пустого тома выполняется
`db/init.sql`; тестовых записей в SQL нет.

## Подготовка и запуск

Нужен работающий Docker Desktop с Compose v2. Для проверочного скрипта на хосте
нужен Python 3 (на целевом Mac уже установлен). См. [окружение](../docs/local-setup.md).
Все следующие команды выполняются из `homework-02/`:

```sh
cp .env.example .env
# Для повторного запуска сохраняйте существующий .env.
docker compose config --quiet
docker compose up -d --build --wait --wait-timeout 120
docker compose ps
```

`.env.example` содержит только локальные демонстрационные параметры. `.env` исключён
из Git. Смена пароля в `.env` не меняет пароль уже инициализированной БД: сохраняйте
настройки вместе с существующим томом либо сознательно выполняйте полный сброс.

## Запросы через entry point

```sh
curl --fail http://127.0.0.1:8082/health
curl --fail -X POST http://127.0.0.1:8082/items \
  -H 'Content-Type: application/json' -d '{"name":"Моя первая запись"}'
curl --fail http://127.0.0.1:8082/items
```

POST возвращает HTTP 201 и JSON с `id` и `name`; GET возвращает список записей из БД.
Пустое имя, имя длиннее 200 символов и неизвестные поля возвращают HTTP 422.
Swagger UI: http://127.0.0.1:8082/docs. Приложение учебное, без аутентификации;
порт ограничен loopback-интерфейсом хоста.

## Проверки

Быстрая проверка двух сервисов, создания/чтения записи и неверного ввода:

```sh
python3 scripts/verify.py
```

Проверка сохранности создаёт уникальную запись через HTTP, затем проверяет тот же
`id` и `name` после restart и после down/up. Данные тома не удаляются. Скрипт
останавливает только эту лабораторную; не запускайте его параллельно с другой её проверкой.

```sh
python3 scripts/verify.py --persistence
```

Интеграционные pytest-тесты используют настоящую PostgreSQL. Override заменяет
entrypoint тестовым процессом; третьего сервиса нет. Тесты удаляют только созданную
ими запись. Для override с `!reset` нужен Compose 2.24.4 или новее.

```sh
docker compose -f compose.yaml -f compose.test.yaml up --build \
  --abort-on-container-exit --exit-code-from entrypoint
# Вернуть обычное HTTP-приложение после тестов:
docker compose up -d --build --wait --wait-timeout 120
```

Успешный скрипт печатает `PASS`, pytest завершается с кодом 0.
Ошибка любой проверки приводит к ненулевому коду выхода.

## Остановка и очистка

Остановить контейнеры, сохранив данные:

```sh
docker compose down
```

Вернуть систему с теми же данными:

```sh
docker compose up -d --wait --wait-timeout 120
```

Полный сброс **безвозвратно удаляет записи этой лабораторной**:

```sh
docker compose down -v
```

## Диагностика и сдача

`docker compose logs entrypoint db` показывает логи. Если занят порт 8082,
остановите использующий его процесс или измените mapping и URL проверок согласованно.
Проверка `/health` обращается к БД, а не только к процессу HTTP.

Материалы: этот README, `Dockerfile`, `db/Dockerfile`, SQL, `compose.yaml`, приложение,
тесты и проверочный скрипт. Ссылка Docker Hub со звёздочкой в задании рассматривается
как дополнительный пункт; публикация в Docker Hub в этот этап не входит.

## Результаты проверки — 21 ноября 2026

Проверено на macOS ARM64, Docker Engine 29.9.3 / Compose 5.7.0:

- Сборка обоих Dockerfile и `docker compose config --quiet` — успешно.
- Два сервиса `db` и `entrypoint` — healthy.
- POST/GET через HTTP — успешно; неверный ввод — HTTP 422.
- Запись `id=1`, `verify-f2056430-9884-45e1-8469-e032da3b6140` сохранилась
  после restart и down/up без удаления тома.
- pytest с реальной PostgreSQL: **8 passed**. Есть одно предупреждение Starlette
  о будущей замене httpx на httpx2; на результат тестов не влияет.
- После тестов обычные контейнеры пересозданы по README; smoke-проверка повторена.

Использованные базовые образы:

- Python `3.13.9-slim-bookworm`, manifest digest
  `sha256:b685a4fa58bb19d1814d78a1ec0f0208f351452724f78b20212c984d6e124a34`.
- PostgreSQL `17.12-bookworm`, manifest digest
  `sha256:837bed18782820fe967067cb5328b02b0d9992c1be9a37ee0c9c492cfc03af3b`.
