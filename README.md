# 🌸 Telegram-бот «Нихао-тян» (NihaoTelegramBotOnPython)

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![Aiogram](https://img.shields.io/badge/Aiogram-3.4.1-2CA5E0?style=flat&logo=telegram&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0_Async-D71F00?style=flat&logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)

Многофункциональный, асинхронный Telegram-бот **«Нихао-тян»**, выполненный на фреймворке **Aiogram 3** и **SQLAlchemy 2.0**. Проект содержит полный набор пользовательских сервисов, административную панель, мультиязычность, систему техподдержки и продакшн-инфраструктуру для развёртывания.

---

## ✨ Основные возможности бота

### 👤 Для пользователей
* **Мгновенный старт и профиль:** Автоматическая регистрация при `/start`, управление личным кабинетом (БИО, статус, роль).
* **🌐 Мультиязычность (RU / EN):** Полноценная локализация на базе Fluent (`aiogram-i18n`). Язык переключается в профиле и сохраняется в БД.
* **🎫 Система техподдержки:** Пошаговая подача тикетов (FSM) с сохранением обращений в базе данных и уведомлением администраторов.
* **🖼️ Каталог и медиа-контент:** Вложенные инлайн-меню для просмотра образов и галереи.

### 🛡️ Для администраторов (`/admin`)
* **📊 Статистика в реальном времени:** Подсчёт пользователей, заблокированных аккаунтов и открытых обращений техподдержки.
* **📢 Безопасная рассылка:** Отправка текстовых и медиа-сообщений (фото, видео, стикеры) всем пользователям с защитой от ошибок блокировки бота.
* **🚫 Блокировка / Разблокировка:** Управление доступом пользователей по Telegram ID с защитой от бана администраторов.
* **📂 Экспорт логов:** Скачивание актуальных логов `bot.log` непосредственно из чата с ботом.

---

## 🛠️ Стек технологий и архитектура

* **Core:** Python 3.10+, [Aiogram 3.4.1](https://github.com/aiogram/aiogram)
* **ORM & Database:** [SQLAlchemy 2.0 Async](https://github.com/sqlalchemy/sqlalchemy), [aiosqlite](https://github.com/nbraud/aiosqlite) (совместимо с PostgreSQL / `asyncpg`), [Alembic](https://github.com/sqlalchemy/alembic) для миграций.
* **Конфигурация:** [Pydantic Settings](https://github.com/pydantic/pydantic-settings) (загрузка и валидация `.env`).
* **Логирование & Алерты:** `logging` с посуточной ротацией файлов + отправка краш-отчетов администраторам в Telegram.
* **Middlewares:** 
  * `DbSessionMiddleware` — сессия БД инжектируется автоматически в каждый хендлер.
  * `BanMiddleware` — авторегистрация и прерывание запросов от заблокированных пользователей.
  * `ThrottlingMiddleware` — защита от флуда и спама.
  * `I18nMiddleware` — динамическая подгрузка языка пользователя.

---

## 📂 Файловая структура проекта

```
NihaoTelegramBotOnPython/
│
├── bot.py                      # Точка входа: инициализация Bot, Dispatcher, middlewares и роутеров.
├── .env.example                # Пример файла переменных окружения.
├── requirements.txt            # Зависимости Python.
├── alembic.ini                 # Конфигурация миграций Alembic.
├── Dockerfile                  # Сборка Docker-образа.
├── docker-compose.yml          # Скрипт запуска в Docker Compose.
│
├── alembic/                    # Миграции структуры базы данных.
├── commands/                   # 👈 Все пользовательские команды (/start, /dedinside, profile, support).
├── config/                     # Настройки проекта (Pydantic Settings).
├── data/                       # Хранилище базы данных SQLite (nihao_chan.db).
├── database/                   # Модели SQLAlchemy (users, tickets, bot_texts) и репозитории (CRUD).
├── filters/                    # Фильтры прав (IsAdmin, IsPrivate).
├── keyboards/                  # Глобальные инлайн-клавиатуры (меню, профиль, админка, отмена).
├── locales/                    # Файлы переводов Fluent (.ftl) для ru и en.
├── middlewares/                # Прослойки (БД, баны, i18n, антифлуд, логирование).
├── routers/                    # Админ-панель и служебные роутеры (admin, errors).
├── utils/                      # Логирование, DynamicTextManager и валидаторы.
└── tests/                      # Набор автоматических тестов (pytest).
```

---

## 🚀 Быстрый запуск

### 1. Клонирование и установка зависимостей
```bash
git clone https://github.com/mi6gin/NihaoTelegramBotOnPython.git
cd NihaoTelegramBotOnPython

# Создание и активация виртуального окружения
python -m venv venv
source venv/bin/activate  # Для macOS/Linux
# venv\Scripts\activate   # Для Windows

# Установка библиотек
pip install -r requirements.txt
```

### 2. Настройка окружения
Создайте файл `.env` на основе примера:
```bash
cp .env.example .env
```
Заполните параметры в `.env`:
* `BOT_TOKEN` — токен вашего бота от [@BotFather](https://t.me/BotFather).
* `ADMIN_IDS` — ваш Telegram ID (узнать в [@userinfobot](https://t.me/userinfobot)).
* `DB_URL` — строка подключения к БД (по умолчанию `sqlite+aiosqlite:///data/nihao_chan.db`).
* `THROTTLING_DELAY` — задержка антифлуда (например, `0.8`).

### 3. Локальный запуск
```bash
python bot.py
```

### 4. Запуск в Docker (Продакшн)
```bash
docker compose up -d --build
```
В Docker-контейнере автоматически применяются миграции Alembic (`alembic upgrade head`), а данные БД и логов пробрасываются через volumes.

---

## 🧪 Тестирование

Проект полностью покрыт автоматическими тестами `pytest`:
```bash
pytest
```

---

## 📜 Лицензия
Проект распространяется под лицензией MIT.

