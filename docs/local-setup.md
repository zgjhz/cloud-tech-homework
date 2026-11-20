# Локальное окружение

Целевая машина: macOS 26.6.2, Apple Silicon (arm64), 16 GiB RAM.
Перед установкой было свободно около 55 GiB. Homebrew 7.0.14 уже установлен.
Базы данных и Python-приложения запускаются в контейнерах, системный Python не меняется.

## Docker Desktop

Установить официальный Docker Desktop для Apple Silicon через Homebrew:

```sh
brew install --cask docker-desktop
open -a Docker
```

Завершить первоначальную настройку Docker Desktop и дождаться запуска Engine.
Официальная инструкция: https://docs.docker.com/desktop/setup/install/mac-install/

Проверить клиент, сервер, Compose и запуск контейнера:

```sh
docker version
docker compose version
docker run --rm hello-world
```

Если `docker` не найден, открыть новый терминал или добавить пользовательские CLI
в PATH текущего терминала: `export PATH="$HOME/.docker/bin:$PATH"`.
Если клиент установлен, но сервер недоступен, запустить Docker Desktop и проверить
выбранный context командами `docker context ls` и `docker context show`.
Не переключать context на удалённый daemon: лабораторные рассчитаны на локальный Docker.

Не запускать все лабораторные одновременно. Обычный `docker compose down`
останавливает сервисы и сохраняет именованные тома; `down -v` удаляет их данные.
Не использовать глобальные prune-команды для очистки отдельной ДЗ.

## Последующие работы

kubectl и minikube устанавливаются перед ДЗ 3. PostgreSQL и RabbitMQ отдельно
на Mac не устанавливаются. GitLab Runner на Mac для выбранного hosted CI не требуется.

## Проверено 21 ноября 2026

Docker Desktop 4.99.0 (245822), Engine/CLI 29.9.3, Compose 5.7.0.
Контекст `desktop-linux`, сервер linux/arm64. `hello-world` выполнен успешно.
Установка завершена копированием официального Docker.app в /Applications после
выдачи разрешений macOS; подпись проверена `codesign --verify --deep --strict`.
Homebrew может запросить пароль администратора для системных ссылок.

В терминале агента использован постоянный путь CLI:

```sh
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
docker version
docker compose version
docker run --rm hello-world
```
