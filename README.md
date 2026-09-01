# Battleship REST Service

Базовый каркас REST-сервиса, разработанный на FastAPI.

На текущем этапе проект включает: запуск приложения и PostgreSQL через Docker Compose; миграции базы данных с помощью Alembic; базовый эндпоинт `POST /games` и автоматические тесты.

## Технологии

- Python 3.11
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Docker Compose
- pytest

## Требования

Для запуска проекта необходимы:

- Docker
- Docker Compose

## Запуск проекта

Собрать и запустить приложение вместе с PostgreSQL:

```
docker compose up --build
```

После запуска API будет доступен по адресу:

http://127.0.0.1:8000

Swagger-документация:

http://127.0.0.1:8000/docs

## Тесты

Для запуска тестов внутри работающего контейнера приложения:

```
docker compose exec app pytest
```

## Миграции

При запуске проекта миграции Alembic применяются автоматически.

Для ручного применения миграций:

```
docker compose run --rm app alembic upgrade head
```

## Остановка проекта

Остановить и удалить запущенные контейнеры:

```
docker compose down
```

Для полной очистки вместе с данными PostgreSQL:

```
docker compose down -v
```