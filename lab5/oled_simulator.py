"""
oled_simulator.py — запускає твій main.py на ПК

Як користуватись:
  1. Пиши код у main.py (як на реальному Pico)
  2. Запускай: python oled_simulator.py

Симулятор автоматично:
  - підставляє фейкові модулі machine / OLED_1inch5 / time
  - знаходить усі функції frame_*() у main.py
  - керує ними через кнопки / клавіші

Клавіші:  ← → або кнопки Prev / Next    Escape — вийти
"""

import sys
import ast
import types
import threading
import tkinter as tk

# ═══════════════════════════════════════════════════════════════
#  ДИСПЛЕЙ-СИМУЛЯТОР
# ═══════════════════════════════════════════════════════════════
class _Display:
    WIDTH  = 128
    HEIGHT = 128
    SCALE  = 4
    white  = 15
    black  = 0

    def __init__(self):
        self._buf = [[0] * self.WIDTH for _ in range(self.HEIGHT)]
        self._skip      = threading.Event()
        self._direction = 1

        # ── Вікно ─────────────────────────────────────────────
        self._root = tk.Tk()
        self._root.title("OLED Simulator  ·  SSD1327  128×128  GS4")
        self._root.resizable(False, False)
        self._root.configure(bg="#12122a")

        tk.Label(self._root,
                 text="OLED 1.5\"  SSD1327  128×128  GS4",
                 fg="#8888cc", bg="#12122a",
                 font=("Courier", 11, "bold")).pack(pady=(10, 4))

        frame_c = tk.Frame(self._root, bg="#444", bd=3, relief="sunken")
        frame_c.pack(padx=16)

        W = self.WIDTH  * self.SCALE
        H = self.HEIGHT * self.SCALE
        self._canvas = tk.Canvas(frame_c, width=W, height=H,
                                 bg="#000", highlightthickness=0)
        self._canvas.pack()

        # ── Індикатор поточного режиму ─────────────────────────
        self._mode_var = tk.StringVar(value="Завантаження…")
        tk.Label(self._root, textvariable=self._mode_var,
                 fg="#ccccff", bg="#12122a",
                 font=("Courier", 10)).pack(pady=(6, 2))

        # ── Кнопки ────────────────────────────────────────────
        btn_f = tk.Frame(self._root, bg="#12122a")
        btn_f.pack(pady=(2, 14))
        kw = dict(font=("Courier", 11, "bold"), width=10,
                  bg="#252560", fg="#ffffff",
                  activebackground="#4444aa", relief="flat", cursor="hand2")
        tk.Button(btn_f, text="◀  Prev",
                  command=self._prev, **kw).pack(side="left", padx=8)
        tk.Button(btn_f, text="Next  ▶",
                  command=self._next, **kw).pack(side="left", padx=8)

        self._root.bind("<Left>",   lambda e: self._prev())
        self._root.bind("<Right>",  lambda e: self._next())
        self._root.bind("<Escape>", lambda e: self._root.destroy())

        # ── PhotoImage — один об'єкт замість 16 384 прямокутників ─
        self._img = tk.PhotoImage(width=W, height=H)
        self._canvas.create_image(0, 0, anchor="nw", image=self._img)
        # Палітра GS4 (0-15) → hex-рядок для PhotoImage.put()
        self._palette = ["#{:02x}{:02x}{:02x}".format(v,v,v)
                         for v in (c * 17 for c in range(16))]
        self._root.update()

    def _prev(self): self._direction = -1; self._skip.set()
    def _next(self): self._direction =  1; self._skip.set()

    def set_label(self, text: str):
        self._mode_var.set(text)

    # ── interruptible sleep ───────────────────────────────────
    def wait(self, seconds: float):
        self._skip.wait(timeout=seconds)

    # ── GS4 → hex ─────────────────────────────────────────────
    @staticmethod
    def _g(c):
        v = max(0, min(15, int(c))) * 17
        return f"#{v:02x}{v:02x}{v:02x}"

    # ══ OLED API ══════════════════════════════════════════════
    def fill(self, c):
        v = max(0, min(15, c))
        for y in range(self.HEIGHT):
            self._buf[y] = [v] * self.WIDTH

    def pixel(self, x, y, c):
        if 0 <= x < self.WIDTH and 0 <= y < self.HEIGHT:
            self._buf[y][x] = max(0, min(15, c))

    def hline(self, x, y, w, c):
        for i in range(w): self.pixel(x+i, y, c)

    def vline(self, x, y, h, c):
        for i in range(h): self.pixel(x, y+i, c)

    def line(self, x1, y1, x2, y2, c):
        dx=abs(x2-x1); dy=abs(y2-y1)
        sx=1 if x1<x2 else -1; sy=1 if y1<y2 else -1
        err=dx-dy
        while True:
            self.pixel(x1,y1,c)
            if x1==x2 and y1==y2: break
            e2=2*err
            if e2>-dy: err-=dy; x1+=sx
            if e2< dx: err+=dx; y1+=sy

    def rect(self, x, y, w, h, c, fill=False):
        if fill:
            for r in range(h): self.hline(x, y+r, w, c)
        else:
            self.hline(x, y, w, c); self.hline(x, y+h-1, w, c)
            self.vline(x, y, h, c); self.vline(x+w-1, y, h, c)

    _FONT = {
        ' ':[0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],
        '!':[0x18,0x3C,0x3C,0x18,0x18,0x00,0x18,0x00],
        '#':[0x36,0x36,0x7F,0x36,0x7F,0x36,0x36,0x00],
        '.':[0x00,0x00,0x00,0x00,0x00,0x18,0x18,0x00],
        ':':[0x00,0x18,0x18,0x00,0x18,0x18,0x00,0x00],
        '-':[0x00,0x00,0x00,0x7E,0x00,0x00,0x00,0x00],
        '/':[0x06,0x0C,0x18,0x30,0x60,0x40,0x00,0x00],
        '0':[0x3C,0x66,0x6E,0x76,0x66,0x66,0x3C,0x00],
        '1':[0x18,0x38,0x18,0x18,0x18,0x18,0x7E,0x00],
        '2':[0x3C,0x66,0x06,0x1C,0x30,0x66,0x7E,0x00],
        '3':[0x3C,0x66,0x06,0x1C,0x06,0x66,0x3C,0x00],
        '4':[0x0C,0x1C,0x3C,0x6C,0x7E,0x0C,0x0C,0x00],
        '5':[0x7E,0x60,0x7C,0x06,0x06,0x66,0x3C,0x00],
        '6':[0x1C,0x30,0x60,0x7C,0x66,0x66,0x3C,0x00],
        '7':[0x7E,0x66,0x0C,0x18,0x18,0x18,0x18,0x00],
        '8':[0x3C,0x66,0x66,0x3C,0x66,0x66,0x3C,0x00],
        '9':[0x3C,0x66,0x66,0x3E,0x06,0x0C,0x38,0x00],
        'A':[0x18,0x3C,0x66,0x7E,0x66,0x66,0x66,0x00],
        'B':[0x7C,0x66,0x66,0x7C,0x66,0x66,0x7C,0x00],
        'C':[0x3C,0x66,0x60,0x60,0x60,0x66,0x3C,0x00],
        'D':[0x78,0x6C,0x66,0x66,0x66,0x6C,0x78,0x00],
        'E':[0x7E,0x60,0x60,0x78,0x60,0x60,0x7E,0x00],
        'F':[0x7E,0x60,0x60,0x78,0x60,0x60,0x60,0x00],
        'G':[0x3C,0x66,0x60,0x6E,0x66,0x66,0x3C,0x00],
        'H':[0x66,0x66,0x66,0x7E,0x66,0x66,0x66,0x00],
        'I':[0x3C,0x18,0x18,0x18,0x18,0x18,0x3C,0x00],
        'J':[0x1E,0x0C,0x0C,0x0C,0x0C,0x6C,0x38,0x00],
        'K':[0x66,0x6C,0x78,0x70,0x78,0x6C,0x66,0x00],
        'L':[0x60,0x60,0x60,0x60,0x60,0x60,0x7E,0x00],
        'M':[0x63,0x77,0x7F,0x6B,0x63,0x63,0x63,0x00],
        'N':[0x66,0x76,0x7E,0x7E,0x6E,0x66,0x66,0x00],
        'O':[0x3C,0x66,0x66,0x66,0x66,0x66,0x3C,0x00],
        'P':[0x7C,0x66,0x66,0x7C,0x60,0x60,0x60,0x00],
        'Q':[0x3C,0x66,0x66,0x66,0x6E,0x3C,0x06,0x00],
        'R':[0x7C,0x66,0x66,0x7C,0x6C,0x66,0x66,0x00],
        'S':[0x3C,0x66,0x60,0x3C,0x06,0x66,0x3C,0x00],
        'T':[0x7E,0x18,0x18,0x18,0x18,0x18,0x18,0x00],
        'U':[0x66,0x66,0x66,0x66,0x66,0x66,0x3C,0x00],
        'V':[0x66,0x66,0x66,0x66,0x66,0x3C,0x18,0x00],
        'W':[0x63,0x63,0x63,0x6B,0x7F,0x77,0x63,0x00],
        'X':[0x66,0x66,0x3C,0x18,0x3C,0x66,0x66,0x00],
        'Y':[0x66,0x66,0x66,0x3C,0x18,0x18,0x18,0x00],
        'Z':[0x7E,0x06,0x0C,0x18,0x30,0x60,0x7E,0x00],
        'a':[0x00,0x00,0x3C,0x06,0x3E,0x66,0x3E,0x00],
        'b':[0x60,0x60,0x7C,0x66,0x66,0x66,0x7C,0x00],
        'c':[0x00,0x00,0x3C,0x60,0x60,0x60,0x3C,0x00],
        'd':[0x06,0x06,0x3E,0x66,0x66,0x66,0x3E,0x00],
        'e':[0x00,0x00,0x3C,0x66,0x7E,0x60,0x3C,0x00],
        'f':[0x1C,0x30,0x30,0x7C,0x30,0x30,0x30,0x00],
        'g':[0x00,0x00,0x3E,0x66,0x66,0x3E,0x06,0x3C],
        'h':[0x60,0x60,0x7C,0x66,0x66,0x66,0x66,0x00],
        'i':[0x18,0x00,0x38,0x18,0x18,0x18,0x3C,0x00],
        'k':[0x60,0x60,0x66,0x6C,0x78,0x6C,0x66,0x00],
        'l':[0x38,0x18,0x18,0x18,0x18,0x18,0x3C,0x00],
        'm':[0x00,0x00,0x63,0x77,0x7F,0x6B,0x63,0x00],
        'n':[0x00,0x00,0x7C,0x66,0x66,0x66,0x66,0x00],
        'o':[0x00,0x00,0x3C,0x66,0x66,0x66,0x3C,0x00],
        'p':[0x00,0x00,0x7C,0x66,0x66,0x7C,0x60,0x60],
        'r':[0x00,0x00,0x7C,0x66,0x60,0x60,0x60,0x00],
        's':[0x00,0x00,0x3E,0x60,0x3C,0x06,0x7C,0x00],
        't':[0x30,0x30,0x7C,0x30,0x30,0x30,0x1C,0x00],
        'u':[0x00,0x00,0x66,0x66,0x66,0x66,0x3E,0x00],
        'v':[0x00,0x00,0x66,0x66,0x66,0x3C,0x18,0x00],
        'w':[0x00,0x00,0x63,0x6B,0x7F,0x77,0x63,0x00],
        'x':[0x00,0x00,0x66,0x3C,0x18,0x3C,0x66,0x00],
        'y':[0x00,0x00,0x66,0x66,0x3E,0x06,0x3C,0x00],
        'z':[0x00,0x00,0x7E,0x0C,0x18,0x30,0x7E,0x00],
        # ── Кирилиця (літери для "СМАРАГДОВЕ НЕБО") ──────────
        'А':[0x18,0x3C,0x66,0x7E,0x66,0x66,0x66,0x00],
        'Б':[0x7E,0x60,0x60,0x7C,0x66,0x66,0x3C,0x00],
        'В':[0x7C,0x66,0x66,0x7C,0x66,0x66,0x7C,0x00],
        'Г':[0x7E,0x60,0x60,0x60,0x60,0x60,0x60,0x00],
        'Д':[0x1E,0x36,0x36,0x36,0x36,0x7F,0x63,0x00],
        'Е':[0x7E,0x60,0x60,0x78,0x60,0x60,0x7E,0x00],
        'М':[0x63,0x77,0x7F,0x6B,0x63,0x63,0x63,0x00],
        'Н':[0x66,0x66,0x66,0x7E,0x66,0x66,0x66,0x00],
        'О':[0x3C,0x66,0x66,0x66,0x66,0x66,0x3C,0x00],
        'Р':[0x7C,0x66,0x66,0x7C,0x60,0x60,0x60,0x00],
        'С':[0x3C,0x66,0x60,0x60,0x60,0x66,0x3C,0x00],
    }

    def text(self, s, x, y, c=15):
        for ch in s:
            glyph = self._FONT.get(ch, self._FONT[' '])
            for row, byte in enumerate(glyph):
                for col in range(8):
                    if byte & (0x80 >> col):
                        self.pixel(x+col, y+row, c)
            x += 8

    def show(self):
        S = self.SCALE
        pal = self._palette
        buf = self._buf
        # Будуємо один рядок даних для PhotoImage.put()
        # Кожен піксель розтягуємо SCALE разів по горизонталі,
        # кожен рядок — SCALE разів по вертикалі
        rows = []
        for y in range(self.HEIGHT):
            row_colors = [pal[buf[y][x]] for x in range(self.WIDTH)]
            # розтягуємо по горизонталі
            stretched = " ".join(c for c in row_colors for _ in range(S))
            # повторюємо рядок SCALE разів
            for _ in range(S):
                rows.append("{" + stretched + "}")
        self._img.put(" ".join(rows))
        self._root.update()


# ═══════════════════════════════════════════════════════════════
#  ПАТЧ sys.modules — підміняємо machine / OLED_1inch5 / time
# ═══════════════════════════════════════════════════════════════
display = _Display()

# ── machine ───────────────────────────────────────────────────
class _Pin:
    OUT = 1
    def __init__(self, *a, **kw): pass
    def __call__(self, *a): pass

class _I2C:
    def __init__(self, *a, **kw): pass

_machine = types.ModuleType('machine')
_machine.Pin     = _Pin
_machine.SoftI2C = _I2C
_machine.I2C     = _I2C
sys.modules['machine'] = _machine

# ── OLED_1inch5 — повертає наш display ────────────────────────
class _OLED_Wrapper:
    """Клас-обгортка: при створенні повертає display."""
    def __new__(cls, *a, **kw):
        return display          # головне — повернути наш об'єкт

_oled_mod = types.ModuleType('OLED_1inch5')
_oled_mod.OLED_1inch5 = _OLED_Wrapper
sys.modules['OLED_1inch5'] = _oled_mod

# ── time — sleep() → display.wait() ──────────────────────────
import time as _real_time
_time_mod = types.ModuleType('time')
_time_mod.sleep    = display.wait
_time_mod.sleep_ms = lambda ms: display.wait(ms / 1000)
_time_mod.ticks_ms = _real_time.time
_time_mod.time     = _real_time.time
sys.modules['time'] = _time_mod

# ═══════════════════════════════════════════════════════════════
#  ЗАВАНТАЖЕННЯ main.py через AST
#  — виконуємо все КРІМ верхньорівневих while-циклів
#    (вони замінюються нашим контролером)
# ═══════════════════════════════════════════════════════════════
MAIN_FILE = 'main.py'

try:
    source = open(MAIN_FILE, encoding='utf-8').read()
except FileNotFoundError:
    print(f"[simulator] Файл '{MAIN_FILE}' не знайдено поруч з oled_simulator.py")
    sys.exit(1)

tree = ast.parse(source, filename=MAIN_FILE)

# Розділяємо: ініціалізація vs while-цикли верхнього рівня
init_nodes, _loop_nodes = [], []
for node in tree.body:
    if isinstance(node, ast.While):
        _loop_nodes.append(node)
    else:
        init_nodes.append(node)

# Виконуємо ініціалізацію (імпорти, змінні, def frame_*…)
ns = {}
exec(compile(ast.Module(body=init_nodes, type_ignores=[]),
             MAIN_FILE, 'exec'), ns)

# ── Збираємо frame_* функції у порядку визначення ─────────────
frames = sorted(
    [(name, fn) for name, fn in ns.items()
     if callable(fn) and (
         name.startswith('frame_') or name.startswith('task')
     )],
    key=lambda nf: nf[1].__code__.co_firstlineno
)

if not frames:
    print("[simulator] Не знайдено жодної функції.")
    print("  Назви функції як: frame_*()  або  task*()")
    sys.exit(1)

print(f"[simulator] Знайдено режими: {[n for n,_ in frames]}")

# ═══════════════════════════════════════════════════════════════
#  ГОЛОВНИЙ ЦИКЛ СИМУЛЯТОРА
# ═══════════════════════════════════════════════════════════════
current = [0]

def run_loop():
    total = len(frames)
    while True:
        display._skip.clear()
        name, fn = frames[current[0]]
        display.set_label(f"{current[0]+1}/{total}  —  {name}()")
        try:
            fn()
        except tk.TclError:
            break   # вікно закрито
        # після завершення (або переривання) — рухаємось далі
        current[0] = (current[0] + display._direction) % total
        display._direction = 1

threading.Thread(target=run_loop, daemon=True).start()
display._root.mainloop()