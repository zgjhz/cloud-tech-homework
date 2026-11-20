# ДЗ 6 — проверки и публикация образа в GitLab.com

CI проверяет приложение [ДЗ 2](../homework-02/README.md), затем публикует его
HTTP entry point в Container Registry. Автоматический deploy не требуется.

## Проект и доступ

- [Приватный проект](https://gitlab.com/kpp-group1/cloud-tech-homework), default branch `main`.
- [Pipelines ветки main](https://gitlab.com/kpp-group1/cloud-tech-homework/-/pipelines?ref=main).
- [Container Registry](https://gitlab.com/kpp-group1/cloud-tech-homework/container_registry).
- Образ: `registry.gitlab.com/kpp-group1/cloud-tech-homework:<полный-SHA>`.
- GitHub `origin` сохранён; дополнительный remote `gitlab`:
  `https://gitlab.com/kpp-group1/cloud-tech-homework.git`.

Проверяющему нужен доступ к приватному проекту. Для работы с API установлен
GitLab CLI 1.131.0 (`brew install glab`). Вход через `glab auth login --hostname
 gitlab.com --web --git-protocol https --setup-git-credential-helper` сохраняет
авторизацию в macOS Keychain. Токены не помещаются в репозиторий.

## Локальные проверки

Из корня репозитория при запущенном Docker Desktop:

```sh
docker compose -f homework-06/compose.yaml build checks
docker compose -f homework-06/compose.yaml run --rm --no-deps checks python -m ruff check --no-cache app tests scripts
docker compose -f homework-06/compose.yaml run --rm checks python -m pytest -q -p no:cacheprovider tests
# Повторный запуск допустим: тесты удаляют собственную запись.
docker compose -f homework-06/compose.yaml run --rm checks python -m pytest -q -p no:cacheprovider tests
docker compose -f homework-06/compose.yaml down
```

PostgreSQL `homework_ci` изолирован от ДЗ 2, без порта на хосте. Данные находятся
в tmpfs и исчезают при остановке контейнера. Пароль в Compose/CI — публичное
значение исключительно для этой одноразовой БД. Fixture ждёт соединения,
создаёт схему из ДЗ 2 и запрещает инициализацию базы с другим именем.

В GitLab выполняются те же команды Ruff/pytest на Python 3.13.9;
Ruff 0.17.6, pytest 9.2.0 и остальные прямые зависимости закреплены в requirements.
Локально подтверждены Ruff и два запуска по 8 успешных тестов. Starlette выдаёт
одно предупреждение о будущем переходе TestClient с httpx на httpx2.

## Pipeline

[Корневой .gitlab-ci.yml](../.gitlab-ci.yml) использует hosted Linux runner
`saas-linux-small-amd64`. Установка runner на Mac не нужна.

1. `lint`: статический анализ приложения, тестов и проверочного скрипта.
2. `test`: API-тесты с PostgreSQL 17.12 как service; проверяются health,
   запись/чтение через API и SQL, отклонение шести вариантов неверного ввода.
3. `publish`: зависит от успешных `lint` и `test`, существует только в pipeline
   default branch. Docker CLI и DinD имеют одинаковую версию 29.9.3;
   соединение использует TLS на 2376 с клиентскими сертификатами.

Для веток и MR запускаются проверки; дублирующий push pipeline открытого MR
подавляется. Теги не запускают pipeline. Публикация использует встроенные
`CI_REGISTRY*`, `docker login --password-stdin` и полный `CI_COMMIT_SHA`.
Собирается именно `--target runtime` из Dockerfile ДЗ 2, а не финальная тестовая
стадия. OCI label `org.opencontainers.image.revision` содержит тот же SHA.
Образ CI — `linux/amd64`. На Apple Silicon он запускается через эмуляцию.

## Скачать и проверить опубликованный образ

После успешного pipeline своего коммита задайте полный SHA. Для приватного
Registry выполните `docker login registry.gitlab.com` с вашим GitLab username
и токеном с правом `read_registry` в интерактивном запросе пароля (не в команде).
Docker Desktop сохраняет авторизацию в credential store.

```sh
export HOMEWORK_SHA="$(git rev-parse HEAD)"
export HOMEWORK_IMAGE="registry.gitlab.com/kpp-group1/cloud-tech-homework:$HOMEWORK_SHA"
docker pull --platform linux/amd64 "$HOMEWORK_IMAGE"
docker image inspect "$HOMEWORK_IMAGE" --format '{{.Architecture}} {{index .Config.Labels "org.opencontainers.image.revision"}} {{json .RepoDigests}}'
docker compose -f homework-06/compose.registry.yaml up -d --build --wait --wait-timeout 120
python3 homework-06/smoke.py
docker compose -f homework-06/compose.registry.yaml down
```

Сравните label с `HOMEWORK_SHA`, digest с Registry и SHA pipeline. Smoke проверяет
`GET /health`, создание уникальной записи с апострофом, чтение этой записи и
HTTP 422 для пустого имени. Порт — `127.0.0.1:8086`. БД этого smoke также временная;
тома предыдущих домашних работ не используются. Compose собирает только БД,
а приложение запускает из скачанного образа Registry.

## Проверка блокировки публикации

Отдельная ветка `codex/hw06-quality-gate` содержит временный намеренно падающий
pytest-тест. После failed pipeline он удаляется и quality jobs запускаются
снова. Эти демонстрационные коммиты не входят в историю main. В ветке нет
publish job по правилам; дополнительно зависимости `needs` блокируют публикацию
в main при падении любой проверки.

Ссылки на конкретные запуски и подтверждённый digest добавляются после внешних
проверок. До их завершения ДЗ 6 не считается выполненным.

Основа настройки TLS: [официальная документация GitLab DinD](https://docs.gitlab.com/ci/docker/docker_in_docker/).

### Текущее состояние внешней проверки

GitLab CI Lint: `valid: true`, без ошибок и предупреждений. У проекта включены
Registry и shared runners, Linux runner отображается online. Однако первый
[pipeline](https://gitlab.com/kpp-group1/cloud-tech-homework/-/pipelines/3095237675)
не создал jobs: API вернул `Identity verification is required in order to run CI jobs`.
Владелец аккаунта должен завершить проверку личности, предложенную GitLab.
Этот failed pipeline не является доказательством срабатывания quality gate.
Публикация образа и smoke из Registry пока не выполнены.
