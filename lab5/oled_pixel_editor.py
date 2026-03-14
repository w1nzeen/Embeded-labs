"""
OLED Pixel Editor — автономний редактор пікселів для SSD1327
Запуск: python oled_pixel_editor.py

Збереження: File > Save code  або  Ctrl+S
"""

import tkinter as tk
from tkinter import messagebox
import os

COLS   = 128
ROWS   = 128
SCALE  = 4
W      = COLS * SCALE   # 512
H      = ROWS * SCALE   # 512
OUTPUT = "oled_drawing.py"

# ─────────────────────────────────────────────────────────────
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("OLED Pixel Editor  ·  SSD1327  128×128  GS4")
        self.root.resizable(False, False)
        self.root.configure(bg="#1a1a2e")

        self.pixels     = [[0] * COLS for _ in range(ROWS)]
        self.history    = []
        self.code_lines = []
        self.tool       = tk.StringVar(value="pixel")
        self.brightness = tk.IntVar(value=15)
        self.start      = None   # (x, y) першої точки для multi-click tools
        self.drawing    = False
        self._status    = tk.StringVar(value="Готово")

        self._build_menu()
        self._build_toolbar()
        self._build_main()
        self._build_statusbar()

        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-s>", lambda e: self.save_code())

        self.render()

    # ── Меню ──────────────────────────────────────────────────
    def _build_menu(self):
        mb = tk.Menu(self.root, bg="#1a1a2e", fg="#ccc",
                     activebackground="#333", activeforeground="#fff",
                     relief="flat")
        self.root.config(menu=mb)

        fm = tk.Menu(mb, tearoff=0, bg="#1a1a2e", fg="#ccc",
                     activebackground="#333", activeforeground="#fff")
        mb.add_cascade(label="File", menu=fm)
        fm.add_command(label="Save code   Ctrl+S", command=self.save_code)
        fm.add_command(label="Clear canvas",       command=self.clear)
        fm.add_separator()
        fm.add_command(label="Exit",               command=self.root.destroy)

        em = tk.Menu(mb, tearoff=0, bg="#1a1a2e", fg="#ccc",
                     activebackground="#333", activeforeground="#fff")
        mb.add_cascade(label="Edit", menu=em)
        em.add_command(label="Undo   Ctrl+Z", command=self.undo)

    # ── Toolbar ───────────────────────────────────────────────
    def _build_toolbar(self):
        bar = tk.Frame(self.root, bg="#1a1a2e", pady=6)
        bar.pack(fill="x", padx=10)

        lbl = lambda t: tk.Label(bar, text=t, fg="#888", bg="#1a1a2e",
                                 font=("Courier", 10))

        # Інструменти
        lbl("Інструмент:").pack(side="left", padx=(0,4))
        tools = [
            ("Піксель",  "pixel"),
            ("Лінія",    "line"),
            ("Hline",    "hline"),
            ("Vline",    "vline"),
            ("Rect",     "rect"),
            ("Rect fill","fill-rect"),
            ("Заливка",  "flood"),
        ]
        self._tool_btns = {}
        for label, val in tools:
            b = tk.Button(bar, text=label, font=("Courier", 10),
                          bg="#252555", fg="#ccc", relief="flat",
                          padx=8, pady=2, cursor="hand2",
                          command=lambda v=val: self.set_tool(v))
            b.pack(side="left", padx=2)
            self._tool_btns[val] = b

        # Роздільник
        tk.Frame(bar, width=1, height=20, bg="#444").pack(side="left", padx=8)

        # Яскравість
        lbl("c=").pack(side="left", padx=(0,4))
        sc = tk.Scale(bar, variable=self.brightness, from_=1, to=15,
                      orient="horizontal", length=100, showvalue=True,
                      bg="#1a1a2e", fg="#ccc", troughcolor="#333",
                      highlightthickness=0, font=("Courier", 9),
                      command=lambda _: self._update_swatch())
        sc.pack(side="left")
        self._swatch = tk.Label(bar, width=3, height=1, bg="#ffffff",
                                relief="solid", bd=1)
        self._swatch.pack(side="left", padx=6)

        # Роздільник
        tk.Frame(bar, width=1, height=20, bg="#444").pack(side="left", padx=8)

        # Кнопки
        for text, cmd in [("Undo ↩", self.undo), ("Очистити", self.clear),
                          ("💾 Зберегти", self.save_code)]:
            tk.Button(bar, text=text, font=("Courier", 10),
                      bg="#252555", fg="#ccc", relief="flat",
                      padx=8, pady=2, cursor="hand2",
                      command=cmd).pack(side="left", padx=2)

        self.set_tool("pixel")
        self._update_swatch()

    # ── Основна область ───────────────────────────────────────
    def _build_main(self):
        frame = tk.Frame(self.root, bg="#1a1a2e")
        frame.pack(padx=10, pady=4, fill="both")

        # Canvas
        cf = tk.Frame(frame, bg="#333", bd=2, relief="sunken")
        cf.pack(side="left")
        self.canvas = tk.Canvas(cf, width=W, height=H,
                                bg="#000", cursor="crosshair",
                                highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Motion>",        self._on_move)
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<ButtonRelease-1>",self._on_release)
        self.canvas.bind("<Leave>",         self._on_leave)

        # Бічна панель
        side = tk.Frame(frame, bg="#1a1a2e", padx=10)
        side.pack(side="left", fill="y")

        tk.Label(side, text="Координати", fg="#888", bg="#1a1a2e",
                 font=("Courier", 10, "bold")).pack(anchor="w")
        self._coord_var = tk.StringVar(value="x = —\ny = —")
        tk.Label(side, textvariable=self._coord_var,
                 fg="#fff", bg="#111", font=("Courier", 12),
                 justify="left", padx=10, pady=8,
                 relief="flat", width=18).pack(anchor="w", pady=(2,10))

        tk.Label(side, text="Згенерований код:", fg="#888", bg="#1a1a2e",
                 font=("Courier", 10, "bold")).pack(anchor="w")

        code_frame = tk.Frame(side, bg="#111")
        code_frame.pack(fill="both", expand=True)
        sb = tk.Scrollbar(code_frame)
        sb.pack(side="right", fill="y")
        self._code_text = tk.Text(code_frame, width=32, height=24,
                                  bg="#111", fg="#7ec8a0",
                                  font=("Courier", 10), relief="flat",
                                  yscrollcommand=sb.set, state="disabled",
                                  padx=8, pady=6)
        self._code_text.pack(side="left", fill="both")
        sb.config(command=self._code_text.yview)

        self._update_code_panel()

    # ── Статусбар ─────────────────────────────────────────────
    def _build_statusbar(self):
        self._status = tk.StringVar(value="Готово")
        tk.Label(self.root, textvariable=self._status,
                 fg="#666", bg="#1a1a2e", font=("Courier", 9),
                 anchor="w", padx=10).pack(fill="x", pady=(0,4))

    # ── Рендер ────────────────────────────────────────────────
    def render(self, preview=None):
        self.canvas.delete("all")
        # Пікселі
        for y in range(ROWS):
            for x in range(COLS):
                c = self.pixels[y][x]
                if c > 0:
                    col = self._gs(c)
                    self.canvas.create_rectangle(
                        x*SCALE, y*SCALE,
                        x*SCALE+SCALE, y*SCALE+SCALE,
                        fill=col, outline="")
        # Попередній перегляд
        if preview:
            for px, py, pc in preview:
                if 0 <= px < COLS and 0 <= py < ROWS:
                    col = self._gs(pc)
                    self.canvas.create_rectangle(
                        px*SCALE, py*SCALE,
                        px*SCALE+SCALE, py*SCALE+SCALE,
                        fill=col, outline="", stipple="gray50")
        # Сітка (тільки кожні 8 пікселів для читабельності)
        for i in range(0, COLS+1, 8):
            self.canvas.create_line(i*SCALE, 0, i*SCALE, H,
                                    fill="#1a1a1a", width=1)
        for j in range(0, ROWS+1, 8):
            self.canvas.create_line(0, j*SCALE, W, j*SCALE,
                                    fill="#1a1a1a", width=1)
        # Центральні лінії
        self.canvas.create_line(W//2, 0, W//2, H, fill="#2a2a3a", width=1)
        self.canvas.create_line(0, H//2, W, H//2, fill="#2a2a3a", width=1)

    @staticmethod
    def _gs(c):
        v = max(0, min(15, c)) * 17
        return f"#{v:02x}{v:02x}{v:02x}"

    def _update_swatch(self):
        v = self.brightness.get() * 17
        self._swatch.config(bg=f"#{v:02x}{v:02x}{v:02x}")

    def set_tool(self, t):
        self.tool.set(t)
        self.start = None
        for k, b in self._tool_btns.items():
            b.config(bg="#252555" if k != t else "#4444aa",
                     fg="#ccc"    if k != t else "#fff")
        self._status.set(f"Інструмент: {t}")

    # ── Mouse events ──────────────────────────────────────────
    def _xy(self, event):
        return event.x // SCALE, event.y // SCALE

    def _on_move(self, event):
        x, y = self._xy(event)
        if not (0 <= x < COLS and 0 <= y < ROWS):
            return
        self._coord_var.set(f"x = {x}\ny = {y}")
        prev = self._get_preview(x, y)
        if self.drawing and self.tool.get() == "pixel":
            self._commit(x, y)
        self.render(preview=prev)

    def _on_press(self, event):
        x, y = self._xy(event)
        if not (0 <= x < COLS and 0 <= y < ROWS):
            return
        self.drawing = True
        t = self.tool.get()
        if t == "pixel":
            self._commit(x, y)
            self.render()
        elif t == "flood":
            self._flood_fill(x, y)
            self.render()
        else:
            if self.start is None:
                self.start = (x, y)
                self._status.set(f"Початок: ({x}, {y}) — клікни другу точку")
            else:
                self._commit(x, y)
                self.start = None
                self.render()

    def _on_release(self, event):
        self.drawing = False

    def _on_leave(self, event):
        self.render()

    # ── Генерація коду / малювання ────────────────────────────
    def _get_preview(self, ex, ey):
        c = self.brightness.get()
        t = self.tool.get()
        if t == "pixel": return [(ex, ey, c)]
        if self.start is None: return []
        sx, sy = self.start
        if t == "line":
            return [(px, py, c) for px, py in self._bresenham(sx, sy, ex, ey)]
        if t == "hline":
            x0, x1 = min(sx, ex), max(sx, ex)
            return [(xx, sy, c) for xx in range(x0, x1+1)]
        if t == "vline":
            y0, y1 = min(sy, ey), max(sy, ey)
            return [(sx, yy, c) for yy in range(y0, y1+1)]
        if t in ("rect", "fill-rect"):
            x0, x1 = min(sx, ex), max(sx, ex)
            y0, y1 = min(sy, ey), max(sy, ey)
            pts = []
            if t == "fill-rect":
                for yy in range(y0, y1+1):
                    for xx in range(x0, x1+1):
                        pts.append((xx, yy, c))
            else:
                for xx in range(x0, x1+1):
                    pts += [(xx, y0, c), (xx, y1, c)]
                for yy in range(y0, y1+1):
                    pts += [(x0, yy, c), (x1, yy, c)]
            return pts
        return []

    def _commit(self, ex, ey):
        c  = self.brightness.get()
        t  = self.tool.get()
        sx = self.start[0] if self.start else ex
        sy = self.start[1] if self.start else ey

        # Зберігаємо snapshot для undo
        self.history.append([row[:] for row in self.pixels])

        pts = self._get_preview(ex, ey)
        for px, py, pc in pts:
            if 0 <= px < COLS and 0 <= py < ROWS:
                self.pixels[py][px] = pc

        # Генеруємо рядок коду
        line = self._gen_code(t, sx, sy, ex, ey, c)
        if line:
            self.code_lines.append(line)
            self._update_code_panel()

    def _gen_code(self, t, sx, sy, ex, ey, c):
        if t == "pixel":   return f"OLED.pixel({ex}, {ey}, {c})"
        if t == "line":    return f"OLED.line({sx}, {sy}, {ex}, {ey}, {c})"
        if t == "hline":
            x0 = min(sx, ex); w = abs(ex - sx) + 1
            return f"OLED.hline({x0}, {sy}, {w}, {c})"
        if t == "vline":
            y0 = min(sy, ey); h = abs(ey - sy) + 1
            return f"OLED.vline({sx}, {y0}, {h}, {c})"
        if t in ("rect", "fill-rect"):
            x0 = min(sx, ex); y0 = min(sy, ey)
            w  = abs(ex - sx) + 1; h = abs(ey - sy) + 1
            if t == "fill-rect":
                return f"OLED.rect({x0}, {y0}, {w}, {h}, {c}, True)"
            return f"OLED.rect({x0}, {y0}, {w}, {h}, {c})"
        return ""

    def _flood_fill(self, sx, sy):
        c    = self.brightness.get()
        old  = self.pixels[sy][sx]
        if old == c: return
        self.history.append([row[:] for row in self.pixels])
        stack = [(sx, sy)]
        while stack:
            x, y = stack.pop()
            if not (0 <= x < COLS and 0 <= y < ROWS): continue
            if self.pixels[y][x] != old: continue
            self.pixels[y][x] = c
            stack += [(x+1,y),(x-1,y),(x,y+1),(x,y-1)]
        self.code_lines.append(f"# flood fill ({sx},{sy}) → c={c}")
        self._update_code_panel()

    @staticmethod
    def _bresenham(x1, y1, x2, y2):
        pts = []
        dx, dy = abs(x2-x1), abs(y2-y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        while True:
            pts.append((x1, y1))
            if x1 == x2 and y1 == y2: break
            e2 = 2 * err
            if e2 > -dy: err -= dy; x1 += sx
            if e2 <  dx: err += dx; y1 += sy
        return pts

    # ── Панель коду ───────────────────────────────────────────
    def _update_code_panel(self):
        self._code_text.config(state="normal")
        self._code_text.delete("1.0", "end")
        if self.code_lines:
            code = "OLED.fill(0)\n" + "\n".join(self.code_lines) + "\nOLED.show()"
        else:
            code = "# намалюй щось\n# код з'явиться тут"
        self._code_text.insert("end", code)
        self._code_text.config(state="disabled")
        self._code_text.see("end")

    # ── Дії ───────────────────────────────────────────────────
    def undo(self):
        if not self.history: return
        self.pixels = self.history.pop()
        if self.code_lines: self.code_lines.pop()
        self._update_code_panel()
        self.render()
        self._status.set("Undo виконано")

    def clear(self):
        if not any(self.pixels[y][x] for y in range(ROWS) for x in range(COLS)):
            return
        self.history.append([row[:] for row in self.pixels])
        self.pixels = [[0]*COLS for _ in range(ROWS)]
        self.code_lines = []
        self.start = None
        self._update_code_panel()
        self.render()
        self._status.set("Полотно очищено")

    def save_code(self):
        if not self.code_lines:
            messagebox.showinfo("Збереження", "Нічого зберігати — полотно порожнє.")
            return
        code = (
            "# Згенеровано OLED Pixel Editor\n"
            "# Вставте цей код у свою функцію task*() або frame_*()\n\n"
            "OLED.fill(0)\n"
            + "\n".join(self.code_lines)
            + "\nOLED.show()\n"
        )
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUTPUT)
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        self._status.set(f"Збережено → {OUTPUT}")
        messagebox.showinfo("Збережено", f"Код збережено у файл:\n{path}")


# ─────────────────────────────────────────────────────────────
root = tk.Tk()
App(root)
root.mainloop()