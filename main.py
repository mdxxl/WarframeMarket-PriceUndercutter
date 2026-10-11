#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Warframe Market Price Undercutter
Автоматически определяет лоты на продажу, находит минимальные цены активных конкурентов
и снижает цену вашего лота на 1 платину ниже самого дешёвого предложения.
"""

import sys
import os
import time
import json
import re
import argparse
from typing import Dict, List, Optional, Any
import requests

# Настройка кодировки вывода для корректного отображения русских символов в консоли Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def log(msg: str = "", **kwargs):
    """Вывод сообщений с немедленным сбросом буфера."""
    print(msg, flush=True, **kwargs)


class WarframeMarketBot:
    BASE_URL = "https://warframe.market"
    API_V2_URL = "https://api.warframe.market/v2"

    def __init__(self, config: dict):
        self.config = config
        self.auth_cfg = config.get("auth", {})
        self.settings = config.get("settings", {})

        self.email = self.auth_cfg.get("email")
        self.password = self.auth_cfg.get("password")
        self.jwt_token = self.auth_cfg.get("token") or self.auth_cfg.get("jwt_token")

        self.competitor_statuses = self.settings.get("competitor_statuses", ["ingame"])
        self.undercut_amount = self.settings.get("undercut_amount", 1)
        self.min_price_floor = self.settings.get("min_price_floor", 1)
        self.platform = self.settings.get("platform", "pc")
        self.crossplay = str(self.settings.get("crossplay", True)).lower()
        self.language = self.settings.get("language", "ru")

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Language": self.language,
            "Platform": self.platform,
            "Crossplay": self.crossplay
        })

        self.csrf_token: Optional[str] = None
        self.user_profile: Optional[dict] = None
        self.items_catalog: Dict[str, dict] = {}  # item_id -> {'slug': str, 'name': str}

    def _sleep_rate_limit(self, delay: float = 0.35):
        """Соблюдение лимита API (макс. 3 запроса в секунду)."""
        time.sleep(delay)

    def login(self) -> bool:
        """
        Аутентификация для работы с API v2.
        Поддерживает:
        1. Прямую передачу JWT токена через config.json ("token": "...") -> чистое v2 API.
        2. Автоматическое получение токена сессии по email и паролю.
        После установки Bearer токена профиль игрока загружается через эндпоинт GET /v2/me.
        """
        if self.jwt_token:
            log("[*] Использование готового токена (Bearer) из конфигурации...")
            self.session.headers["Authorization"] = f"Bearer {self.jwt_token}"
            return self.fetch_profile_v2()

        if not self.email or not self.password:
            log("[!] Укажите email и пароль в локальном config.json или задайте Bearer/JWT-токен.")
            return False

        log("[*] Получение сессии и CSRF-токена с warframe.market...")
        try:
            r0 = self.session.get(self.BASE_URL, timeout=15)
            r0.raise_for_status()
            match = re.search(r'<meta\s+name=["\']csrf-token["\']\s+content=["\']([^"\']+)["\']', r0.text)
            if not match:
                log("[!] Ошибка: Не удалось найти csrf-token в мета-тегах страницы.")
                return False
            self.csrf_token = match.group(1)
        except Exception as e:
            log(f"[!] Ошибка подключения к сайту: {e}")
            return False

        log(f"[*] Авторизация под учётной записью: {self.email}...")
        login_payload = {
            "email": self.email,
            "password": self.password,
            "auth_type": "cookie"
        }
        login_headers = {
            "Content-Type": "application/json",
            "X-CSRFToken": self.csrf_token
        }

        try:
            resp = self.session.post(
                "https://api.warframe.market/v1/auth/signin",
                json=login_payload,
                headers=login_headers,
                timeout=15
            )
            if resp.status_code != 200:
                log(f"[!] Ошибка входа (статус {resp.status_code}): {resp.text}")
                return False

            # Извлекаем JWT токен и устанавливаем Bearer заголовок для всех запросов к API v2
            self.jwt_token = self.session.cookies.get("JWT")
            if self.jwt_token:
                self.session.headers["Authorization"] = f"Bearer {self.jwt_token}"

            return self.fetch_profile_v2()
        except Exception as e:
            log(f"[!] Исключение при авторизации: {e}")
            return False

    def fetch_profile_v2(self) -> bool:
        """Загрузка профиля игрока через API v2: GET /v2/me."""
        log("[*] Запрос профиля пользователя через API v2 (GET /v2/me)...")
        self._sleep_rate_limit()
        try:
            resp = self.session.get(f"{self.API_V2_URL}/me", timeout=15)
            if resp.status_code != 200:
                log(f"[!] Ошибка получения профиля через GET /v2/me (HTTP {resp.status_code}): {resp.text}")
                return False
            data = resp.json().get("data", {})
            self.user_profile = data
            ingame_name = data.get("ingameName", data.get("slug", "Unknown"))
            reputation = data.get("reputation", 0)
            log(f"[✓] Успешная авторизация в API v2! Игрок: {ingame_name} (Репутация: {reputation})")
            return True
        except Exception as e:
            log(f"[!] Исключение при получении профиля /v2/me: {e}")
            return False

    def load_items_catalog(self) -> bool:
        """Загружает полный справочник предметов для быстрого сопоставления itemId -> slug и названия."""
        log("[*] Загрузка каталога предметов Warframe.market...")
        self._sleep_rate_limit()
        try:
            resp = self.session.get(f"{self.API_V2_URL}/items", timeout=20)
            resp.raise_for_status()
            items = resp.json().get("data", [])
            for itm in items:
                itm_id = itm.get("id")
                slug = itm.get("slug")
                i18n = itm.get("i18n", {})
                # Берем русское название, если нет — английское
                ru_info = i18n.get("ru", {})
                en_info = i18n.get("en", {})
                name = ru_info.get("name") or en_info.get("name") or slug
                self.items_catalog[itm_id] = {
                    "slug": slug,
                    "name": name
                }
            log(f"[✓] Каталог предметов загружен ({len(self.items_catalog)} позиций).")
            return True
        except Exception as e:
            log(f"[!] Ошибка загрузки каталога предметов: {e}")
            return False

    def get_my_sell_orders(self) -> List[dict]:
        """Возвращает список активных лотов пользователя на продажу."""
        self._sleep_rate_limit()
        try:
            resp = self.session.get(f"{self.API_V2_URL}/orders/my", timeout=15)
            resp.raise_for_status()
            orders = resp.json().get("data", [])
            # Фильтруем только лоты на продажу (sell)
            sell_orders = [o for o in orders if o.get("type") == "sell" and o.get("visible", True)]
            return sell_orders
        except Exception as e:
            log(f"[!] Ошибка получения ваших лотов: {e}")
            return []

    def get_competitor_orders(self, item_slug: str, my_order: dict) -> List[dict]:
        """
        Запрашивает все предложения других игроков по предмету
        и отбирает подходящих конкурентов.
        """
        self._sleep_rate_limit()
        url = f"{self.API_V2_URL}/orders/item/{item_slug}"
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return []
            all_orders = resp.json().get("data", [])
        except Exception as e:
            log(f"[!] Ошибка при запросе предложений для {item_slug}: {e}")
            return []

        my_id = my_order.get("id")
        my_user_id = self.user_profile.get("id")
        my_slug = self.user_profile.get("slug")

        my_rank = my_order.get("rank")
        my_amber = my_order.get("amberStars")
        my_cyan = my_order.get("cyanStars")
        my_subtype = my_order.get("subtype")

        valid_competitors = []
        for o in all_orders:
            # Только продажа
            if o.get("type") != "sell":
                continue
            # Только видимые
            if not o.get("visible", True):
                continue
            # Исключаем свой собственный заказ
            if o.get("id") == my_id:
                continue
            user_info = o.get("user", {})
            if user_info.get("id") == my_user_id or user_info.get("slug") == my_slug:
                continue

            # Фильтр по статусу конкурента (ingame, online)
            user_status = user_info.get("status")
            if user_status not in self.competitor_statuses:
                continue

            # Проверка соответствия атрибутов (ранг мода, звёзды скульптур)
            if my_rank is not None and o.get("rank") != my_rank:
                continue
            if my_amber is not None and o.get("amberStars") != my_amber:
                continue
            if my_cyan is not None and o.get("cyanStars") != my_cyan:
                continue
            if my_subtype is not None and o.get("subtype") != my_subtype:
                continue

            valid_competitors.append(o)

        return valid_competitors

    def update_order_price(self, order: dict, new_price: int) -> bool:
        """Обновляет цену лота через PATCH /v2/order/{id}."""
        self._sleep_rate_limit()
        order_id = order.get("id")
        patch_url = f"{self.API_V2_URL}/order/{order_id}"

        # Для изменения цены отправляем только platinum
        payload: Dict[str, Any] = {
            "platinum": new_price
        }

        headers = {
            "Content-Type": "application/json"
        }
        if self.csrf_token:
            headers["X-CSRFToken"] = self.csrf_token

        try:
            resp = self.session.patch(patch_url, json=payload, headers=headers, timeout=15)
            if resp.status_code == 200:
                order["platinum"] = new_price
                return True
            else:
                log(f"    [!] Ошибка обновления цены (HTTP {resp.status_code}): {resp.text}")
                return False
        except Exception as e:
            log(f"    [!] Исключение при обновлении цены: {e}")
            return False

    def sync_prices(self):
        """Основной цикл проверки и синхронизации цен всех лотов."""
        log("\n" + "=" * 70)
        log(f"[*] Начало проверки цен ({time.strftime('%Y-%m-%d %H:%M:%S')})")
        log(f"[*] Учитываемые статусы конкурентов: {self.competitor_statuses}")
        log("=" * 70)

        my_orders = self.get_my_sell_orders()
        if not my_orders:
            log("[!] Активных лотов на продажу не обнаружено.")
            return

        log(f"[i] Найдено ваших активных лотов на продажу: {len(my_orders)}\n")

        updated_count = 0
        unchanged_count = 0
        no_competitors_count = 0

        for idx, order in enumerate(my_orders, 1):
            order_id = order.get("id")
            item_id = order.get("itemId")
            curr_plat = order.get("platinum")
            qty = order.get("quantity", 1)

            # Получаем слаг и имя предмета из каталога
            item_info = self.items_catalog.get(item_id, {})
            item_slug = item_info.get("slug")
            item_name = item_info.get("name", item_slug or item_id)

            # Дополнительное описание (ранг, звёзды)
            extra_desc = []
            if order.get("rank") is not None:
                extra_desc.append(f"Ранг {order['rank']}")
            if order.get("amberStars") is not None or order.get("cyanStars") is not None:
                extra_desc.append(f"Звёзды: {order.get('amberStars', 0)}я/{order.get('cyanStars', 0)}г")
            extra_str = f" ({', '.join(extra_desc)})" if extra_desc else ""

            header_line = f"[{idx:2d}/{len(my_orders)}] {item_name}{extra_str}"
            log(header_line)

            if not item_slug:
                log(f"    [!] Пропуск: Не удалось определить slug для itemId {item_id}")
                continue

            # Получаем конкурентов
            competitors = self.get_competitor_orders(item_slug, order)

            if not competitors:
                log(f"    Текущая цена: {curr_plat} пл (кол-во: {qty}) | Конкуренты в игре (ingame) отсутствуют.")
                no_competitors_count += 1
                continue

            # Находим минимальную цену конкурента
            cheapest = min(competitors, key=lambda x: x.get("platinum", 999999))
            min_comp_plat = cheapest.get("platinum")
            comp_user = cheapest.get("user", {})
            comp_name = comp_user.get("ingameName", comp_user.get("slug", "неизвестно"))
            comp_status = comp_user.get("status", "")

            # Целевая цена: на undercut_amount меньше минимальной, но не ниже min_price_floor
            target_plat = max(self.min_price_floor, min_comp_plat - self.undercut_amount)

            if target_plat != curr_plat:
                log(f"    Конкурент: {comp_name} ({comp_status}) -> {min_comp_plat} пл")
                log(f"    -> Изменение цены: {curr_plat} пл -> {target_plat} пл (-{self.undercut_amount} пл от конкурента)")
                success = self.update_order_price(order, target_plat)
                if success:
                    log(f"    [✓] Цена успешно обновлена!")
                    updated_count += 1
                else:
                    log(f"    [✗] Не удалось обновить цену.")
            else:
                log(f"    Текущая цена: {curr_plat} пл уже оптимальна (лучшая цена конкурента: {min_comp_plat} пл)")
                unchanged_count += 1

        log("\n" + "-" * 70)
        log(f"[*] Проверка завершена:")
        log(f"    - Обновлено лотов: {updated_count}")
        log(f"    - Без изменений (уже мин. цена): {unchanged_count}")
        log(f"    - Конкурентов не было в игре (ingame): {no_competitors_count}")
        log("-" * 70 + "\n")


def load_config(config_path: str = "config.json") -> dict:
    """Загрузка конфигурации из файла."""
    if not os.path.exists(config_path):
        log(f"[!] Файл конфигурации {config_path} не найден! Создаю шаблон...")
        default_config = {
            "auth": {
                "email": "",
                "password": "",
                "token": ""
            },
            "settings": {
                "competitor_statuses": ["ingame"],
                "undercut_amount": 1,
                "min_price_floor": 1,
                "loop_mode": False,
                "interval_seconds": 300,
                "platform": "pc",
                "crossplay": True,
                "language": "ru"
            }
        }
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        return default_config

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Warframe Market Price Undercutter")
    parser.add_argument("--config", default="config.json", help="Путь к файлу конфигурации")
    parser.add_argument("--loop", action="store_true", help="Включить циклический режим работы")
    parser.add_argument("--interval", type=int, default=None, help="Интервал обновления в секундах при циклическом режиме")
    parser.add_argument("--only-ingame", action="store_true", help="Считать конкурентами только игроков, которые в игре (по умолчанию включено)")
    parser.add_argument("--include-online", action="store_true", help="Учитывать также игроков со статусом 'online' (на сайте, но не в игре)")
    args = parser.parse_args()

    # Загружаем настройки
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.config)
    cfg = load_config(config_path)

    if args.include_online:
        cfg["settings"]["competitor_statuses"] = ["ingame", "online"]
    elif args.only_ingame:
        cfg["settings"]["competitor_statuses"] = ["ingame"]
    if args.loop:
        cfg["settings"]["loop_mode"] = True
    if args.interval:
        cfg["settings"]["interval_seconds"] = args.interval

    bot = WarframeMarketBot(cfg)

    # 1. Авторизация
    if not bot.login():
        log("[!] Не удалось авторизоваться. Завершение работы.")
        sys.exit(1)

    # 2. Загрузка каталога предметов
    if not bot.load_items_catalog():
        log("[!] Не удалось загрузить каталог предметов. Завершение работы.")
        sys.exit(1)

    # 3. Режим работы (однократный или цикл)
    is_loop = cfg["settings"].get("loop_mode", False)
    interval = cfg["settings"].get("interval_seconds", 300)

    if not is_loop:
        bot.sync_prices()
    else:
        log(f"[*] Включен циклический режим. Интервал проверки: {interval} сек.")
        try:
            while True:
                bot.sync_prices()
                log(f"[*] Следующая проверка через {interval} секунд. Для выхода нажмите Ctrl+C...")
                time.sleep(interval)
        except KeyboardInterrupt:
            log("\n[*] Работа бота остановлена пользователем.")


if __name__ == "__main__":
    main()

