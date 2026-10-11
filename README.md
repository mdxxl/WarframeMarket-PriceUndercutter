# 🌌 Warframe Market Price Undercutter

[🇬🇧 English](#english-section) · [🇷🇺 Русский](#русский-раздел)

---
## English section

This Python bot monitors your visible sell orders on [Warframe.market](https://warframe.market), compares them with matching offers from other players, and lowers your price when needed.

### Features

- Loads your profile and active visible sell orders.
- Matches items using the Warframe.market item catalogue.
- Filters competitors by status: `ingame` only, or both `ingame` and `online`.
- Matches mod ranks, Ayatan star counts, and subtypes when those attributes are present on your order.
- Undercuts the lowest matching offer by a configurable platinum amount, while respecting a minimum price floor.
- Runs once or repeats checks at a configured interval.
- Supports email and password authentication or a Bearer/JWT token.

An order is left unchanged when there are no matching competitors or its price already matches the target.

### Installation

Open a terminal in the project directory and install the dependency:

```bash
python -m pip install requests
```

On Windows, use `py` instead of `python` if needed:

```powershell
py -m pip install requests
```

### Configuration

The repository includes `config.json` with empty authentication fields. Enter credentials locally, but never commit a password or token or publish a filled-in config.

```json
{
  "auth": {
    "email": "",
    "password": "",
    "token": ""
  },
  "settings": {
    "competitor_statuses": ["ingame"],
    "undercut_amount": 1,
    "min_price_floor": 1,
    "loop_mode": false,
    "interval_seconds": 300,
    "platform": "pc",
    "crossplay": true,
    "language": "en"
  }
}
```

| Setting | Purpose |
| --- | --- |
| `auth.email` / `auth.password` | Warframe.market sign-in credentials. |
| `auth.token` | Bearer/JWT token; used when provided. |
| `competitor_statuses` | Competitor statuses: `["ingame"]` or `["ingame", "online"]`. |
| `undercut_amount` | Platinum amount to subtract from the lowest matching offer. |
| `min_price_floor` | Minimum price the bot will set. |
| `loop_mode` | `true` enables repeated checks; `false` runs once. |
| `interval_seconds` | Delay between checks in loop mode. |
| `platform`, `crossplay`, `language` | API request settings. |

### How price updates work

1. The bot authenticates and loads your profile.
2. It loads the item catalogue and your visible sell orders.
3. For each order, it finds offers for the same item and filters matching competitors.
4. It calculates the target price as the lowest competitor price minus `undercut_amount`, but never below `min_price_floor`.
5. If the target differs from your current price, the bot updates the order through the API.

Review `undercut_amount`, `min_price_floor`, and competitor statuses before running the bot, especially in loop mode.

### Project structure

```text
warframe_market/
├── main.py       # Authentication, competitor lookup, and order updates
├── config.json   # Project settings with blank authentication fields
├── .gitignore    # Excludes the Python cache
└── README.md     # Russian and English documentation
```

---

## Русский раздел

Бот получает ваши видимые ордера на продажу, сравнивает их с подходящими предложениями других игроков и при необходимости снижает цену относительно самого дешёвого конкурента.

### Возможности

- Загружает профиль и активные видимые ордера на продажу.
- Сопоставляет предметы через каталог Warframe.market.
- Учитывает статус конкурента: только `ingame` или `ingame` и `online`.
- Сравнивает ранги модов, звёзды Аятан и подтипы, если эти параметры есть у вашего ордера.
- Снижает цену на заданное количество платины относительно самого дешёвого подходящего предложения, соблюдая минимальный ценовой порог.
- Работает один раз или повторяет проверку через заданный интервал.
- Поддерживает вход по email и паролю либо Bearer/JWT-токену.

Если подходящих конкурентов нет или цена уже соответствует целевой, ордер не меняется.

### Установка

Откройте терминал в папке проекта и установите зависимость:

```bash
python -m pip install requests
```

В Windows при необходимости используйте `py` вместо `python`:

```powershell
py -m pip install requests
```

### Настройка

В репозитории уже есть `config.json` с пустыми полями авторизации. Укажите данные локально, но не коммитьте пароль или токен и не публикуйте заполненный конфиг.

```json
{
  "auth": {
    "email": "",
    "password": "",
    "token": ""
  },
  "settings": {
    "competitor_statuses": ["ingame"],
    "undercut_amount": 1,
    "min_price_floor": 1,
    "loop_mode": false,
    "interval_seconds": 300,
    "platform": "pc",
    "crossplay": true,
    "language": "ru"
  }
}
```

| Параметр | Назначение |
| --- | --- |
| `auth.email` / `auth.password` | Данные для входа на Warframe.market. |
| `auth.token` | Bearer/JWT-токен; если указан, используется он. |
| `competitor_statuses` | Статусы конкурентов: `["ingame"]` или `["ingame", "online"]`. |
| `undercut_amount` | На сколько платины бот снижает цену относительно самого дешёвого подходящего предложения. |
| `min_price_floor` | Нижний предел цены. |
| `loop_mode` | `true` включает постоянные проверки, `false` — одну проверку. |
| `interval_seconds` | Интервал между проверками в циклическом режиме. |
| `platform`, `crossplay`, `language` | Параметры запросов к API. |

### Как работает изменение цены

1. Бот авторизуется и загружает профиль.
2. Загружает каталог предметов и ваши видимые ордера на продажу.
3. Ищет предложения по тому же предмету и отбирает подходящих конкурентов.
4. Рассчитывает цену: минимальная цена конкурента минус `undercut_amount`, но не ниже `min_price_floor`.
5. Если цена отличается от текущей, отправляет обновление ордера через API.

До запуска проверьте `undercut_amount`, `min_price_floor` и статусы конкурентов, особенно при включённом циклическом режиме.

### Структура проекта

```text
warframe_market/
├── main.py       # Авторизация, поиск конкурентов и обновление ордеров
├── config.json   # Настройки проекта с пустыми полями авторизации
├── .gitignore    # Исключает кэш Python
└── README.md     # Документация на русском и английском
```




