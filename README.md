# Battleship REST Service

Базовый сервис для игры «Морской бой» на FastAPI.

На текущем этапе реализованы:
- запуск приложения и PostgreSQL через Docker Compose;
- миграции базы данных через Alembic;
- генерация стандартного флота из 10 кораблей и 20 палуб;
- проверка состава и корректности расстановки флота;
- проверка границ поля, пересечений и касаний кораблей;
- сохранение игровой сессии и расстановки флота в PostgreSQL;
- маршрут `POST /games`;
- модульные и интеграционные тесты.

## Технологии

- Python 3.11
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Docker Compose
- pytest

## Настройка окружения

Перед запуском создайте файл `.env` на основе `.env.example` и укажите параметры PostgreSQL.

```
Copy-Item .env.example .env
```

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