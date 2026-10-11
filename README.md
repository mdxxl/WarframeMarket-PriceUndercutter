# Warframe Market Price Undercutter

[English](#english) · [Русский](#русский)

## English

A Python script for keeping your sell orders on [Warframe.market](https://warframe.market) below the cheapest matching offer. By default, it checks players who are in game and sets your price 1 platinum lower.

It checks visible sell orders and compares mod ranks, Ayatan stars and subtypes when those details are set on your order. If no matching offers are found, it leaves the price alone.

### Getting started

You need Python and the `requests` library. Open a terminal in the project folder and run:

```bash
python -m pip install requests
```

Open `config.json` and fill in `auth.email` and `auth.password`, or use `auth.token` for a Bearer/JWT token. If a token is set, the script uses it. Keep your filled-in config local; don't commit your password or token.

Then run:

```bash
python main.py
```

On Windows, you can use `py` instead of `python`.

### Settings

The `settings` section in `config.json` controls pricing and how often checks run:

| Setting | What to put here |
| --- | --- |
| `competitor_statuses` | `["ingame"]` for players in game, or `["ingame", "online"]` to include players online on the site. |
| `undercut_amount` | How much cheaper your order should be, in platinum. Default: `1`. |
| `min_price_floor` | The lowest price the script can set. Default: `1`. |
| `loop_mode` | `false` for one check, `true` to keep checking. |
| `interval_seconds` | Seconds between checks in loop mode. Default: `300`. |
| `platform` | Platform sent with API requests. Default: `"pc"`. |
| `crossplay` | Crossplay setting sent with API requests. Default: `true`. |
| `language` | Language sent with API requests, such as `"ru"` or `"en"`. Console messages are in Russian. |

For example, if the cheapest matching offer is 20 platinum and `undercut_amount` is 1, your order becomes 19 platinum. The price never goes below `min_price_floor`.

**The script can also raise prices.** It sets the calculated price whenever it differs from yours, even if yours is already lower. There is no preview step: running it changes orders on your account.

### Repeated checks

Check every five minutes:

```bash
python main.py --loop --interval 300
```

Include players who are online on the site:

```bash
python main.py --include-online
```

You can combine these options. Use `--only-ingame` to restrict checks to players in game, or `--config other-config.json` to load a different config. Stop the loop with Ctrl+C.

## Русский

Скрипт на Python, чтобы не переставлять цены на [Warframe.market](https://warframe.market) вручную. Он проверяет ваши лоты на продажу и ставит цену ниже самого дешёвого подходящего предложения. По умолчанию — на 1 платину, с учётом только игроков в игре.

В проверку попадают видимые лоты. Для модов и скульптур Аятан учитываются ранг, звёзды и подтип, если они указаны у вашего лота. Если подходящих конкурентов нет, цена остаётся прежней.

### Как запустить

Нужны Python и библиотека `requests`. Откройте терминал в папке проекта и выполните:

```bash
python -m pip install requests
```

В `config.json` заполните `auth.email` и `auth.password` либо укажите Bearer/JWT-токен в `auth.token`. Если токен заполнен, скрипт использует его. Конфиг с вашими данными оставьте на своём компьютере — пароль и токен не нужно отправлять в репозиторий.

Запуск:

```bash
python main.py
```

В Windows вместо `python` можно использовать `py`.

### Что настроить

Параметры цены и повторных проверок находятся в разделе `settings` файла `config.json`:

| Параметр | Что указать |
| --- | --- |
| `competitor_statuses` | `["ingame"]` — только игроки в игре; `["ingame", "online"]` — ещё и те, кто онлайн на сайте. |
| `undercut_amount` | На сколько платины дешевле ставить ваш лот. По умолчанию: `1`. |
| `min_price_floor` | Минимальная цена, которую может поставить скрипт. По умолчанию: `1`. |
| `loop_mode` | `false` — проверить один раз, `true` — проверять постоянно. |
| `interval_seconds` | Пауза между проверками в секундах. По умолчанию: `300`. |
| `platform` | Платформа для запросов к API. По умолчанию: `"pc"`. |
| `crossplay` | Настройка кроссплея для запросов к API. По умолчанию: `true`. |
| `language` | Язык запросов к API, например `"ru"` или `"en"`. Сообщения в консоли остаются на русском. |

Например, конкурент продаёт предмет за 20 платины. При `undercut_amount: 1` скрипт выставит ваш лот за 19. Ниже `min_price_floor` цена не опустится.

**Скрипт может и поднять цену.** Если ваш лот уже дешевле рассчитанной цены, он всё равно выставит рассчитанную. Предварительного просмотра нет: после запуска цены меняются сразу в вашем аккаунте.

### Повторные проверки

Проверять цены каждые пять минут:

```bash
python main.py --loop --interval 300
```

Учитывать также игроков со статусом «онлайн на сайте»:

```bash
python main.py --include-online
```

Эти параметры можно совмещать. `--only-ingame` оставляет только игроков в игре, а `--config other-config.json` позволяет выбрать другой конфиг. Чтобы остановить цикл, нажмите Ctrl+C.
