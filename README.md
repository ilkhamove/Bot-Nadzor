# Bot-Nadzor

Телеграм-бот на базе `aiogram 3`, который получает статистику Telegram-каналов через API [Tgstat](https://tgstat.ru/). Бот поддерживает два языка (RU/UZ), умеет показывать краткий отчет и хранит историю запросов пользователя в SQLite.

## Требования
- Python 3.10+
- Установленные переменные окружения:
  - `TELEGRAM_BOT_TOKEN` — токен вашего Telegram-бота.
  - `TGSTAT_API_KEY` — API-ключ Tgstat.
  - `BOT_DATABASE_PATH` — путь к SQLite-базе (опционально, по умолчанию `data/bot.db`).

## Установка
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## Запуск
```bash
export TELEGRAM_BOT_TOKEN=your_telegram_token
export TGSTAT_API_KEY=your_tgstat_api_key
python -m bot.main
```

## Структура проекта
- `bot/main.py` — точка входа бота.
- `bot/config.py` — загрузка настроек из переменных окружения.
- `bot/handlers/` — обработчики команд, основного сценария и истории.
- `bot/services/` — клиент Tgstat и форматирование отчетов.
- `bot/db/` — подключение к SQLite и модели данных.
- `tests/` — простые unit-тесты для форматирования и клиента.

## Тесты
```bash
pytest
```

## Дополнительно
- Обновление статистики и просмотр истории доступны через inline-кнопки.
- TODO: при необходимости адаптировать параметры запроса `channels/get` под актуальную версию API Tgstat.
