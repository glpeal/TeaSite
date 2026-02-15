#!/usr/bin/env python3
"""
Cha-hai Tea Shop — Telegram Notification Bot

Отправляет уведомления владельцу магазина в Telegram,
когда клиент оформляет заказ или оставляет заявку на сайте.

Установка:
    pip install flask requests

Настройка (переменные окружения):
    export TELEGRAM_BOT_TOKEN="токен_от_BotFather"
    export TELEGRAM_CHAT_ID="ваш_числовой_chat_id"

Запуск:
    python bot.py

Как получить токен бота:
    1. Откройте @BotFather в Telegram
    2. Отправьте /newbot
    3. Задайте имя и username бота
    4. Скопируйте токен

Как получить chat_id:
    1. Напишите вашему боту /start
    2. Откройте в браузере:
       https://api.telegram.org/bot<ВАШ_ТОКЕН>/getUpdates
    3. Найдите "chat":{"id": ЧИСЛО} — это ваш chat_id
"""

import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
import requests as http_requests

# ===== НАСТРОЙКИ =====
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 8080))

# Папка с сайтом (index.html, pics/ и т.д.)
SITE_DIR = os.path.dirname(os.path.abspath(__file__))

# ===== ПРИЛОЖЕНИЕ =====
app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("cha-hai-bot")


def send_telegram(text):
    """Отправить сообщение владельцу через Telegram Bot API."""
    if not BOT_TOKEN or not CHAT_ID:
        log.error("BOT_TOKEN или CHAT_ID не настроены!")
        return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        r = http_requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        log.info("Уведомление отправлено в Telegram")
        return True
    except Exception as e:
        log.error(f"Ошибка отправки в Telegram: {e}")
        return False


def format_contact(contact_type, contact):
    """Форматировать строку контакта."""
    if contact_type == "telegram":
        username = contact.lstrip("@")
        return f'Telegram: <a href="https://t.me/{username}">@{username}</a>'
    return f"WhatsApp: {contact}"


@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return response


@app.route("/api/order", methods=["POST", "OPTIONS"])
def handle_order():
    """Обработка заказа из корзины."""
    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"ok": False, "error": "Нет данных"}), 400

    contact_type = data.get("contactType", "telegram")
    contact = data.get("contact", "").strip()
    items = data.get("items", [])
    total = data.get("total", 0)

    if not contact:
        return jsonify({"ok": False, "error": "Укажите контакт"}), 400

    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    ct = format_contact(contact_type, contact)

    lines = [
        "\U0001f6d2 <b>Новый заказ!</b>",
        f"\U0001f4c5 {now}",
        "",
    ]

    if items:
        lines.append("<b>Состав заказа:</b>")
        for it in items:
            name = it.get("name", "")
            detail = it.get("detail", "")
            price = it.get("total", 0)
            lines.append(f"  \u2022 {name} \u2014 {detail} \u2014 {price} \u20bd")
        lines.append("")
        lines.append(f"\U0001f4b0 <b>Итого: {total} \u20bd</b>")
        lines.append("")

    lines.append(f"\U0001f4f1 <b>Контакт:</b> {ct}")
    lines.append("")
    lines.append("\U0001f446 Напишите клиенту!")

    msg = "\n".join(lines)

    if send_telegram(msg):
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Ошибка отправки"}), 500


@app.route("/api/request", methods=["POST", "OPTIONS"])
def handle_request():
    """Обработка быстрой заявки (без корзины)."""
    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"ok": False, "error": "Нет данных"}), 400

    contact_type = data.get("contactType", "telegram")
    contact = data.get("contact", "").strip()
    product_name = data.get("productName", "")
    message = data.get("message", "")

    if not contact:
        return jsonify({"ok": False, "error": "Укажите контакт"}), 400

    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    ct = format_contact(contact_type, contact)

    lines = [
        "\U0001f4e9 <b>Новая заявка!</b>",
        f"\U0001f4c5 {now}",
        "",
    ]

    if product_name:
        lines.append(f"\U0001f375 Интересует: <b>{product_name}</b>")
        lines.append("")

    if message:
        lines.append(f"\U0001f4ac Сообщение: {message}")
        lines.append("")

    lines.append(f"\U0001f4f1 <b>Контакт:</b> {ct}")
    lines.append("")
    lines.append("\U0001f446 Напишите клиенту!")

    msg = "\n".join(lines)

    if send_telegram(msg):
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Ошибка отправки"}), 500


# ===== Раздача файлов сайта =====

@app.route("/")
def serve_index():
    return send_from_directory(SITE_DIR, "index.html")


@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(SITE_DIR, path)


# ===== Запуск =====

if __name__ == "__main__":
    print()
    print("=" * 50)
    print("  Cha-hai Tea Shop — Notification Bot")
    print("=" * 50)

    if not BOT_TOKEN:
        print()
        print("  [!] TELEGRAM_BOT_TOKEN не задан!")
        print("      export TELEGRAM_BOT_TOKEN='токен'")

    if not CHAT_ID:
        print()
        print("  [!] TELEGRAM_CHAT_ID не задан!")
        print("      export TELEGRAM_CHAT_ID='id'")

    if BOT_TOKEN and CHAT_ID:
        print(f"\n  [OK] Бот настроен. Chat ID: {CHAT_ID}")

    print(f"\n  Сервер: http://localhost:{PORT}")
    print(f"  Файлы: {SITE_DIR}")
    print()

    app.run(host=HOST, port=PORT, debug=True)
