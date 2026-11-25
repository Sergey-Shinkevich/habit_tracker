# Habit Tracker ("Атомные привычки")

Бэкенд-сервис для трекинга полезных и приятных привычек в духе книги *«Атомные привычки»* с REST API, JWT-авторизацией, фоновыми задачами на Celery и отправкой напоминаний в Telegram.

## Стек технологий

- **Python** & **Poetry**
- **Django 6.0** & **Django REST Framework (DRF)**
- **PostgreSQL** (основная база данных)
- **Redis** (брокер сообщений и кэш/результаты для Celery)
- **Celery** & **Celery Beat** (асинхронные и периодические задачи по расписанию)
- **JWT (`djangorestframework-simplejwt`)** — авторизация пользователей
- **Telegram Bot API** — отправка уведомлений о привычках
- **drf-yasg** / **drf-spectacular** — документация API (Swagger / ReDoc)
- **flake8** & **coverage** — контроль стиля кода (PEP 8) и покрытия тестами

## Структура проекта

- `user/` — регистрация, аутентификация (JWT), кастомная модель пользователя, права доступа
- `habit/` — модели привычек, валидаторы, CRUD-эндпоинты, пагинация, доступ к чужим/публичным привычкам
- `telegram_bot/` — интеграция с Telegram Bot API, отправка напоминаний, задачи Celery и логика периодичности

## Быстрый старт

### 1. Клонирование и установка зависимостей

```bash
git clone <https://github.com/Sergey-Shinkevich/habit_tracker.git>
cd habit_tracker
poetry install
```

### 2. Настройка переменных окружения

Скопируйте файл примера окружения и заполните значения:

```bash
cp .env.template .env
```

Пример содержимого `.env.template`:

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# База данных
POSTGRES_DB=habit_tracker
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis / Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# JWT
ACCESS_TOKEN_LIFETIME_MINUTES=60
REFRESH_TOKEN_LIFETIME_DAYS=7

# Telegram Bot
TG_BOT_TOKEN=your-telegram-bot-token
```

### 3. Применение миграций и запуск сервера

```bash
poetry run python manage.py migrate
poetry run python manage.py runserver
```

### 4. Запуск Celery Worker и Celery Beat

В отдельных терминалах запустите воркер и планировщик расписания:

```bash
poetry run celery -A config worker -l INFO
poetry run celery -A config beat -l INFO
```

## Документация API

После запуска сервера интерактивная документация эндпоинтов доступна по адресам:

- **Swagger UI:** `http://127.0.0.1:8000/swagger/` 
- **ReDoc:** `http://127.0.0.1:8000/redoc/`

## Тестирование, покрытие кода и линтер

### Запуск тестов с расчётом покрытия

```bash
poetry run coverage erase
poetry run coverage run manage.py test user habit telegram_bot -v 2
poetry run coverage report -m
poetry run coverage html
```

Текущее покрытие кода составляет **96%** (при минимальном пороге **80%**).

### Проверка стиля кода (PEP 8)

```bash
poetry run flake8 . --statistics
```