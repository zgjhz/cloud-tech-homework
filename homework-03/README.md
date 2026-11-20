# ДЗ 3 — frontend/backend в Kubernetes

Frontend Nginx принимает запросы через LoadBalancer на порту 8083 и проксирует
их во внутренний Service `backend:8000`. Backend Deployment имеет две реплики;
каждый ответ содержит hostname обслужившего pod. Сервисы изолированы namespace
`homework-03`. Это учебный HTTP-сервис без аутентификации и БД.

## Окружение

Нужны Docker Desktop, kubectl, minikube и Python 3 для проверки с хоста.
Команды ниже выполняются из корня репозитория:

```sh
export PATH="/opt/homebrew/bin:/Applications/Docker.app/Contents/Resources/bin:$PATH"
brew install kubectl minikube
minikube start -p cloud-homework --driver=docker --cpus=2 --memory=4096 --kubernetes-version=v1.37.0
kubectl --context cloud-homework get nodes
```

На macOS используйте Docker driver. Начальный бюджет — 2 CPU и 4 GiB памяти.
Перед запуском можно остановить ДЗ 2, сохранив её данные:
`docker compose -f homework-02/compose.yaml --env-file homework-02/.env stop`.

## Сборка и развёртывание

```sh
docker build -t cloud-homework/backend:hw03-v1 homework-03/backend
docker build -t cloud-homework/frontend:hw03-v1 homework-03/frontend
minikube image load -p cloud-homework cloud-homework/backend:hw03-v1
minikube image load -p cloud-homework cloud-homework/frontend:hw03-v1
minikube image ls -p cloud-homework
kubectl --context cloud-homework apply -f homework-03/k8s/namespace.yaml
kubectl --context cloud-homework apply -f homework-03/k8s/
kubectl --context cloud-homework -n homework-03 rollout status deployment/backend --timeout=120s
kubectl --context cloud-homework -n homework-03 rollout status deployment/frontend --timeout=120s
kubectl --context cloud-homework -n homework-03 get pods,services
```

Четыре обязательных YAML находятся отдельно: `backend-deployment.yaml`,
`frontend-deployment.yaml`, `backend-service.yaml`, `frontend-service.yaml`.
Readiness/liveness probes и ресурсы заданы для обоих Deployment.
При изменении кода используйте новый тег в сборке и Deployment: `IfNotPresent`
может оставить прежний образ при повторном использовании тега.

## Доступ с компьютера вне кластера

В отдельном терминале оставьте работающий туннель:

```sh
export PATH="/opt/homebrew/bin:/Applications/Docker.app/Contents/Resources/bin:$PATH"
minikube tunnel -p cloud-homework
```

В основном терминале получите IP и отправьте запрос с macOS:

```sh
kubectl --context cloud-homework -n homework-03 get service frontend
FRONTEND_IP=$(kubectl --context cloud-homework -n homework-03 get service frontend -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl --fail "http://${FRONTEND_IP}:8083/demo?source=host"
python3 homework-03/scripts/verify.py
python3 homework-03/scripts/verify.py --replace-pod
```

На Docker driver в macOS адрес LoadBalancer обычно `127.0.0.1`; это доступ с
хоста вне кластера, а не публичный интернет-IP. Без туннеля EXTERNAL-IP может
оставаться pending либо уже назначенный IP перестаёт отвечать. Port-forward
для основной демонстрации не используется. Порт 8083 выбран выше 1024.

Проверка использует независимые соединения и ожидает ответы обеих Ready-реплик,
проверяет заголовок frontend и сохранение пути/параметров запроса. Режим
`--replace-pod` удаляет один backend pod, ожидает новую готовую реплику и повторяет
проверку через внешний frontend. При ошибке скрипт завершается ненулевым кодом.
Непрерывная доступность без единого потерянного запроса при удалении pod не обещается.

## Диагностика и остановка

```sh
kubectl --context cloud-homework -n homework-03 get endpointslices
kubectl --context cloud-homework -n homework-03 logs deployment/frontend
kubectl --context cloud-homework -n homework-03 describe pods
```

При ImagePullBackOff проверьте теги и загрузку образов именно в профиль
`cloud-homework`. При pending IP проверьте работающий `minikube tunnel`.
При занятом порту 8083 остановите процесс, занимающий его, перед запуском туннеля.

Остановить туннель — Ctrl-C в его терминале. Остановить кластер без удаления:

```sh
minikube stop -p cloud-homework
```

Удалить только ресурсы ДЗ 3:

```sh
kubectl --context cloud-homework delete namespace homework-03
```

Повторное развёртывание выполняется командами выше. Полностью удалить учебный
кластер (все ресурсы этого профиля): `minikube delete -p cloud-homework`.
Другие профили и Docker volumes ДЗ 2 эти команды не затрагивают.

## Проверенные результаты — 21 ноября 2026

Окружение: macOS ARM64, Docker Desktop 4.99.0 / Engine 29.9.3,
minikube 1.39.0, kubectl 1.37.2, Kubernetes 1.37.0, containerd 2.3.4.

- Узел `cloud-homework` Ready, backend 2/2, frontend 1/1.
- Backend ClusterIP не имеет внешнего IP; его EndpointSlice содержит два адреса pod.
- Frontend LoadBalancer получил `127.0.0.1`, порт 8083; curl выполнен с macOS.
- Внешние запросы вернули pod `backend-7f594ddfb6-d9tgs` и
  `backend-7f594ddfb6-tjpdh`, заголовок `X-Lab-Frontend: nginx` и исходный путь.
- После удаления `backend-7f594ddfb6-d9tgs` появился Ready pod
  `backend-7f594ddfb6-68z4q`; обе актуальные реплики ответили через frontend.

Имена pod и ClusterIP при повторном запуске меняются. Команды в разделе проверок
получают текущие значения через Kubernetes API.

Базовые образы сборки: Python `3.13.9-slim-bookworm`
(`sha256:b685a4fa58bb19d1814d78a1ec0f0208f351452724f78b20212c984d6e124a34`)
и Nginx `1.28.0-alpine`
(`sha256:30f1c0d78e0ad60901648be663a710bdadf19e4c10ac6782c235200619158284`).

Полное пересоздание namespace по README также проверено: оба Deployment готовы,
внешний IP назначен повторно, скрипт получил ответы от новых pod
`backend-7f594ddfb6-6h5sl` и `backend-7f594ddfb6-87pzx`.
