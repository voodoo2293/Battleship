# Battleship REST Service

Базовый сервис для игры «Морской бой» на FastAPI.

На текущем этапе реализованы:
- запуск приложения и PostgreSQL через Docker Compose;
- начальная миграция базы данных через Alembic;
- маршрут `POST /games`;
- базовые тесты.

## Технологии

- Python 3.11
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Docker Compose
- pytest

## Запуск

Для запуска проекта:

```
docker compose up --build
```

Миграции базы данных применяются автоматически при запуске.

Swagger:

http://127.0.0.1:8000/docs

## Тесты

Для запуска тестов:

```
docker compose exec app pytest
```

## Остановка

Для остановки проекта:

```
docker compose down
```

Для остановки проекта с удалением данных PostgreSQL:

```
docker compose down -v
```