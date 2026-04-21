# server.py — HTTP-сервер на чистих сокетах для MicroPython
#
# Принципи:
#   - Жодних сторонніх фреймворків
#   - Парсинг HTTP вручну, з урахуванням обмежень MicroPython
#   - Кожен маршрут — окрема функція
#   - Обробка помилок у кожній критичній точці

import socket
import json
import time

try:
    import ujson as json_module
except ImportError:
    import json as json_module

from machine import Pin
from state import system_state, get_uptime, get_full_status
from sensors import get_sensor_data
from display_manager import display_message

# ── LED ──────────────────────────────────────────────────────────────
# LED підключений до GP10
_led_pin = Pin(10, Pin.OUT)

def led_on():
    """Вмикає LED і оновлює стан."""
    _led_pin.value(1)
    system_state["led"] = True
    print("[led] Увімкнено")

def led_off():
    """Вимикає LED і оновлює стан."""
    _led_pin.value(0)
    system_state["led"] = False
    print("[led] Вимкнено")

def get_led_state():
    """Повертає поточний стан LED."""
    return system_state["led"]

# ── Файли ────────────────────────────────────────────────────────────

def load_file(path):
    """
    Читає файл з файлової системи Pico W.

    Параметри:
        path — шлях до файлу (напр. 'templates/index.html')

    Повертає:
        str — вміст файлу або None при помилці

    Увага: на Pico W файли мають бути в кореневому каталозі або підпапках.
    """
    try:
        with open(path, "rb") as f:
            return f.read().decode("utf-8")
    except OSError as e:
        print(f"[server] Помилка читання файлу '{path}': {e}")
        return None

def render_index_html():
    """
    Завантажує index.html і підставляє динамічні значення через str.replace().

    Плейсхолдери у HTML:
        {{STATE}}           — LED ON або LED OFF
        {{TEMPERATURE}}     — температура або N/A
        {{HUMIDITY}}        — вологість або N/A
        {{AIR_QUALITY}}     — якість повітря або N/A
        {{LAST_MESSAGE}}    — останнє повідомлення
        {{PROGRAM_ENABLED}} — статус програми
        {{IP}}              — IP-адреса
        {{UPTIME}}          — uptime у секундах

    Повертає:
        str — готовий HTML або запасний рядок при помилці
    """
    template = load_file("templates/index.html")
    if template is None:
        return "<html><body><h1>Помилка: index.html не знайдено</h1></body></html>"

    sensors = system_state["last_sensor_read"]

    def fmt(val, unit=""):
        """Форматує значення сенсора або повертає N/A."""
        if val is None:
            return "N/A"
        return f"{val}{unit}"

    led_state_text = "ON" if system_state["led"] else "OFF"
    program_text   = "Активна" if system_state["program_enabled"] else "Призупинена"

    replacements = {
        "{{STATE}}":                led_state_text,
        "{{LED_CLASS}}":            "led--on" if system_state["led"] else "led--off",
        "{{TEMPERATURE}}":          fmt(sensors.get("temperature"), "°C"),
        "{{HUMIDITY}}":             fmt(sensors.get("humidity"), "%"),
        "{{AIR_QUALITY}}":          fmt(sensors.get("air_quality"), " AQI"),
        "{{LAST_MESSAGE}}":         system_state["last_message"] or "—",
        "{{PROGRAM_ENABLED}}":      program_text,
        "{{PROGRAM_ENABLED_CLASS}}": "badge--active" if system_state["program_enabled"] else "badge--paused",
        "{{IP}}":                   system_state["ip"],
        "{{UPTIME}}":               str(get_uptime()) + "с",
    }

    for placeholder, value in replacements.items():
        template = template.replace(placeholder, str(value))

    return template

# ── HTTP helpers ──────────────────────────────────────────────────────

def send_response(client, body, content_type="text/html", status="200 OK"):
    """
    Надсилає HTTP-відповідь клієнту.

    Параметри:
        client       — socket-з'єднання
        body         — рядок тіла відповіді
        content_type — MIME-тип
        status       — рядок статусу ("200 OK", "404 Not Found", ...)
    """
    if isinstance(body, str):
        body_bytes = body.encode("utf-8")
    else:
        body_bytes = body

    response = (
        f"HTTP/1.1 {status}\r\n"
        f"Content-Type: {content_type}; charset=utf-8\r\n"
        f"Content-Length: {len(body_bytes)}\r\n"
        f"Connection: close\r\n"
        f"\r\n"
    ).encode("utf-8") + body_bytes

    try:
        client.sendall(response)
    except Exception as e:
        print(f"[server] Помилка відправки відповіді: {e}")

def send_redirect(client, location="/"):
    """Надсилає HTTP 302 редірект."""
    response = (
        f"HTTP/1.1 302 Found\r\n"
        f"Location: {location}\r\n"
        f"Connection: close\r\n"
        f"\r\n"
    )
    try:
        client.sendall(response.encode("utf-8"))
    except Exception as e:
        print(f"[server] Помилка редіректу: {e}")

def send_json(client, data, status="200 OK"):
    """Серіалізує dict у JSON і надсилає як відповідь."""
    try:
        body = json_module.dumps(data)
    except Exception as e:
        print(f"[server] Помилка серіалізації JSON: {e}")
        body = '{"error": "json serialization failed"}'
    send_response(client, body, content_type="application/json", status=status)

# ── Парсинг HTTP-запиту ───────────────────────────────────────────────

def parse_request(raw):
    """
    Парсить сирий HTTP-запит.

    Параметри:
        raw — bytes або str, отримані від client.recv()

    Повертає:
        dict з полями:
            "method"  — "GET" / "POST"
            "path"    — шлях без query string
            "query"   — dict параметрів query string
            "body"    — рядок тіла POST-запиту або ""
            "headers" — dict заголовків (ключі в нижньому регістрі)

    Примітки щодо MicroPython:
        - recv() може повернути неповні дані — ми читаємо Content-Length і добираємо тіло
        - re (regex) доступний в MicroPython, але для простоти використовуємо split()
    """
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "ignore")

    result = {
        "method":  "GET",
        "path":    "/",
        "query":   {},
        "body":    "",
        "headers": {}
    }

    try:
        # Розділяємо заголовки і тіло
        if "\r\n\r\n" in raw:
            header_part, body_part = raw.split("\r\n\r\n", 1)
        else:
            header_part = raw
            body_part   = ""

        lines = header_part.split("\r\n")
        if not lines:
            return result

        # ── Рядок запиту (перший рядок) ──
        parts = lines[0].split(" ")
        if len(parts) >= 2:
            result["method"] = parts[0].upper()
            full_path        = parts[1]

            # Розбираємо path і query string
            if "?" in full_path:
                result["path"], qs = full_path.split("?", 1)
                result["query"]    = _parse_query_string(qs)
            else:
                result["path"] = full_path

        # ── Заголовки ──
        for line in lines[1:]:
            if ": " in line:
                key, val = line.split(": ", 1)
                result["headers"][key.lower()] = val.strip()

        result["body"] = body_part

    except Exception as e:
        print(f"[server] Помилка парсингу запиту: {e}")

    return result

def _parse_query_string(qs):
    """Парсить рядок виду 'a=1&b=hello' у {'a': '1', 'b': 'hello'}."""
    params = {}
    if not qs:
        return params
    for pair in qs.split("&"):
        if "=" in pair:
            k, v = pair.split("=", 1)
            params[_url_decode(k)] = _url_decode(v)
    return params

def _url_decode(s):
    """
    Мінімальний URL-decode для MicroPython.
    Обробляє %XX hex-послідовності і '+' → ' '.
    """
    s = s.replace("+", " ")
    result = []
    i = 0
    while i < len(s):
        if s[i] == "%" and i + 2 < len(s):
            try:
                result.append(chr(int(s[i+1:i+3], 16)))
                i += 3
                continue
            except ValueError:
                pass
        result.append(s[i])
        i += 1
    return "".join(result)

def _parse_post_body(body):
    """
    Витягує поля з POST body формату application/x-www-form-urlencoded.
    Повертає dict.
    """
    return _parse_query_string(body.strip())

# ── Маршрути ──────────────────────────────────────────────────────────

def route_index(client, req):
    """GET / — головна сторінка."""
    # Оновлюємо дані сенсорів при кожному відкритті сторінки
    get_sensor_data()
    html = render_index_html()
    send_response(client, html)

def route_led_on(client, req):
    """GET /lighton — вмикає LED і повертає на головну."""
    led_on()
    send_redirect(client, "/")

def route_led_off(client, req):
    """GET /lightoff — вимикає LED і повертає на головну."""
    led_off()
    send_redirect(client, "/")

def route_status(client, req):
    """GET /status — повертає JSON зі станом системи."""
    send_json(client, get_full_status())

def route_sensors(client, req):
    """GET /sensors — повертає JSON з показниками сенсорів."""
    data = get_sensor_data()
    send_json(client, data)

def route_message(client, req):
    """
    POST /message — отримує повідомлення з вебформи.

    Алгоритм:
        1. Зчитуємо Content-Length
        2. Якщо тіло неповне — повертаємо 400
        3. URL-decode
        4. Зберігаємо в system_state["last_message"]
        5. Виводимо на дисплей
        6. Редіректимо на головну
    """
    if req["method"] != "POST":
        send_response(client, "Method Not Allowed", status="405 Method Not Allowed")
        return

    body = req["body"]
    fields = _parse_post_body(body)
    message = fields.get("message", "").strip()

    if message:
        system_state["last_message"] = message[:128]  # Обмеження довжини
        display_message(message)
        print(f"[server] Отримано повідомлення: {message}")
    else:
        print("[server] Порожнє повідомлення — ігнорується")

    send_redirect(client, "/")

def route_toggle_system(client, req):
    """
    GET /toggle-system — перемикає program_enabled.

    Це веб-аналог апаратної кнопки.
    """
    system_state["program_enabled"] = not system_state["program_enabled"]
    state_text = "активована" if system_state["program_enabled"] else "призупинена"
    print(f"[server] Програма {state_text} через веб")
    send_redirect(client, "/")

def route_css(client, req):
    """GET /style.css — повертає CSS-файл."""
    css = load_file("static/style.css")
    if css is None:
        send_response(client, "/* CSS not found */", content_type="text/css", status="404 Not Found")
    else:
        send_response(client, css, content_type="text/css")

def route_not_found(client, req):
    """404 для будь-якого невідомого маршруту."""
    body = (
        "<html><body>"
        "<h1>404 — Сторінку не знайдено</h1>"
        f"<p>Шлях: {req['path']}</p>"
        '<a href="/">← На головну</a>'
        "</body></html>"
    )
    send_response(client, body, status="404 Not Found")

# Таблиця маршрутів: (метод, шлях) → функція-обробник
# Метод None означає "будь-який метод"
ROUTES = {
    ("GET",  "/"):               route_index,
    ("GET",  "/index.html"):     route_index,
    ("GET",  "/lighton"):        route_led_on,
    ("GET",  "/lightoff"):       route_led_off,
    ("GET",  "/status"):         route_status,
    ("GET",  "/sensors"):        route_sensors,
    ("POST", "/message"):        route_message,
    ("GET",  "/toggle-system"):  route_toggle_system,
    ("GET",  "/style.css"):      route_css,
}

# ── Основний цикл сервера ─────────────────────────────────────────────

def handle_client(client):
    """
    Обробляє одне підключення:
        1. Зчитує запит
        2. Парсить його
        3. Диспетчеризує до маршруту
        4. Закриває з'єднання

    Викликається з run_server() при кожному accept().
    """
    try:
        # Встановлюємо таймаут на читання — не блокуємось вічно
        client.settimeout(5.0)
        raw = b""

        # Читаємо заголовки (до \r\n\r\n)
        while b"\r\n\r\n" not in raw:
            chunk = client.recv(1024)
            if not chunk:
                break
            raw += chunk

        req = parse_request(raw)

        # Якщо POST — добираємо тіло згідно з Content-Length
        if req["method"] == "POST":
            content_length = int(req["headers"].get("content-length", 0))
            already_read   = len(req["body"].encode("utf-8"))
            remaining      = content_length - already_read
            while remaining > 0:
                chunk = client.recv(min(remaining, 512))
                if not chunk:
                    break
                req["body"]  += chunk.decode("utf-8", "ignore")
                remaining    -= len(chunk)

        print(f"[server] {req['method']} {req['path']}")

        # Якщо програма вимкнена — відповідаємо статус-сторінкою
        # (обрано варіант: сервер продовжує відповідати, але показує "призупинено")
        # Виняток: /toggle-system і /status завжди доступні
        if not system_state["program_enabled"] and req["path"] not in ("/toggle-system", "/status", "/style.css"):
            paused_html = (
                "<html><head><link rel='stylesheet' href='/style.css'></head>"
                "<body><div class='paused-banner'>"
                "<h1>⏸ Програму призупинено</h1>"
                "<p>Натисніть апаратну кнопку або</p>"
                "<a href='/toggle-system' class='btn'>Активувати через веб</a>"
                "</div></body></html>"
            )
            send_response(client, paused_html)
            return

        # Диспетчер маршрутів
        handler = ROUTES.get((req["method"], req["path"]))
        if handler:
            handler(client, req)
        else:
            route_not_found(client, req)

    except Exception as e:
        print(f"[server] Помилка обробки клієнта: {e}")
        try:
            send_response(client, "<h1>500 Internal Server Error</h1>", status="500 Internal Server Error")
        except:
            pass
    finally:
        try:
            client.close()
        except:
            pass

def run_server(host="0.0.0.0", port=80):
    """
    Запускає HTTP-сервер і слухає підключення.

    Параметри:
        host — адреса прослуховування (0.0.0.0 = всі інтерфейси)
        port — порт (80 — стандартний HTTP)

    Цикл:
        - accept() чекає підключення (блокуючий виклик)
        - handle_client() обробляє запит
        - повторюється нескінченно

    Примітка щодо MicroPython:
        Pico W не підтримує потоки (threading) у стандартній конфігурації,
        тому обробка запитів послідовна — один за одним.
        Для конкурентної обробки потрібно uasyncio (не розглядається тут).
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"[server] HTTP-сервер запущено на {host}:{port}")

    while True:
        try:
            client, addr = server_socket.accept()
            print(f"[server] Підключення від {addr[0]}")
            handle_client(client)
        except OSError as e:
            print(f"[server] Socket помилка accept: {e}")
            time.sleep(0.1)
        except Exception as e:
            print(f"[server] Непередбачена помилка: {e}")
            time.sleep(0.1)
