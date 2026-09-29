"""
rle_app.py - RLE codec for binary images: drawing GUI + file handling.

Run:  python rle_app.py        (needs codec.py in the same folder)

File format (both raw and compressed files):
    bytes 0-1 : width  (big-endian, 16 bits)
    bytes 2-3 : height (big-endian, 16 bits)
    bytes 4.. : raw pixels (width*height bytes)  -> .raw file
                RLE stream (see codec.py)        -> .rle file
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox

from codec import encode, decode

BLACK, WHITE = 0x00, 0xFF
MAX_DIM = 200
HEADER_SIZE = 4


# ---------------------------------------------------------------- file I/O
def _header(w: int, h: int) -> bytes:
    return w.to_bytes(2, "big") + h.to_bytes(2, "big")


def _parse_header(data: bytes):
    if len(data) < HEADER_SIZE:
        raise ValueError("File too short (missing header)")
    w = int.from_bytes(data[0:2], "big")
    h = int.from_bytes(data[2:4], "big")
    if w == 0 or h == 0:
        raise ValueError("Invalid image size in header")
    return w, h, data[HEADER_SIZE:]


def save_raw(path: str, w: int, h: int, pixels: bytes) -> int:
    data = _header(w, h) + pixels
    with open(path, "wb") as f:
        f.write(data)
    return len(data)


def load_raw(path: str):
    with open(path, "rb") as f:
        w, h, pixels = _parse_header(f.read())
    if len(pixels) != w * h:
        raise ValueError("Pixel data size does not match width x height")
    return w, h, pixels


def save_compressed(path: str, w: int, h: int, pixels: bytes) -> int:
    data = _header(w, h) + encode(pixels)
    with open(path, "wb") as f:
        f.write(data)
    return len(data)


def load_compressed(path: str):
    with open(path, "rb") as f:
        w, h, stream = _parse_header(f.read())
    pixels = decode(stream)
    if len(pixels) != w * h:
        raise ValueError("Decoded size does not match width x height "
                         "(corrupted file?)")
    return w, h, pixels


# ------------------------------------------------------------- pixel grid
class PixelGrid(tk.Canvas):
    """A canvas showing a w x h grid of black/white cells."""

    def __init__(self, master, editable: bool, **kw):
        super().__init__(master, bg="#888888", highlightthickness=1,
                         highlightbackground="#444444", **kw)
        self.editable = editable
        self.w = self.h = 0
        self.cell = 10
        self.pixels = bytearray()
        self.rects = []
        if editable:
            self.bind("<Button-1>", lambda e: self._paint(e, BLACK))
            self.bind("<B1-Motion>", lambda e: self._paint(e, BLACK))
            for btn in ("<Button-2>", "<Button-3>"):      # right click (mac/win/linux)
                self.bind(btn, lambda e: self._paint(e, WHITE))
            for mot in ("<B2-Motion>", "<B3-Motion>"):
                self.bind(mot, lambda e: self._paint(e, WHITE))

    def set_image(self, w: int, h: int, pixels: bytes = None):
        self.w, self.h = w, h
        self.cell = max(2, min(20, 400 // max(w, h)))
        self.pixels = bytearray(pixels if pixels is not None
                                else bytes([WHITE]) * (w * h))
        self.config(width=w * self.cell, height=h * self.cell)
        self.delete("all")
        self.rects = []
        c = self.cell
        for y in range(h):
            for x in range(w):
                color = "black" if self.pixels[y * w + x] == BLACK else "white"
                self.rects.append(self.create_rectangle(
                    x * c, y * c, (x + 1) * c, (y + 1) * c,
                    fill=color, outline="#cccccc" if c >= 6 else color))

    def clear(self):
        if self.w:
            self.set_image(self.w, self.h)

    def get_pixels(self) -> bytes:
        return bytes(self.pixels)

    def _paint(self, event, value):
        x = int(self.canvasx(event.x)) // self.cell
        y = int(self.canvasy(event.y)) // self.cell
        if 0 <= x < self.w and 0 <= y < self.h:
            i = y * self.w + x
            if self.pixels[i] != value:
                self.pixels[i] = value
                self.itemconfig(self.rects[i],
                                fill="black" if value == BLACK else "white")


# -------------------------------------------------------------------- app
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RLE Codec - Binary Images")
        self.resizable(True, True)

        # --- top bar: size + actions
        bar = tk.Frame(self, padx=8, pady=8)
        bar.pack(fill="x")

        tk.Label(bar, text="Width:").pack(side="left")
        self.w_var = tk.StringVar(value="32")
        tk.Entry(bar, textvariable=self.w_var, width=5).pack(side="left", padx=(2, 8))
        tk.Label(bar, text="Height:").pack(side="left")
        self.h_var = tk.StringVar(value="32")
        tk.Entry(bar, textvariable=self.h_var, width=5).pack(side="left", padx=(2, 8))

        for text, cmd in [
            ("New", self.new_image),
            ("Clear", self.clear),
            ("Save raw", self.save_raw),
            ("Open raw", self.open_raw),
            ("Compress & save", self.compress),
            ("Open compressed", self.open_compressed),
        ]:
            tk.Button(bar, text=text, command=cmd).pack(side="left", padx=2)

        # --- two canvases
        main = tk.Frame(self, padx=8)
        main.pack()

        left = tk.LabelFrame(main, text="Drawing (left click = black, right click = white)",
                             padx=6, pady=6)
        left.grid(row=0, column=0, padx=6, pady=6, sticky="n")
        self.editor = PixelGrid(left, editable=True)
        self.editor.pack()

        right = tk.LabelFrame(main, text="Decompressed result", padx=6, pady=6)
        right.grid(row=0, column=1, padx=6, pady=6, sticky="n")
        self.viewer = PixelGrid(right, editable=False)
        self.viewer.pack()

        # --- status bar
        self.status = tk.StringVar(value="Draw an image, then use 'Compress & save'.")
        tk.Label(self, textvariable=self.status, anchor="w", justify="left",
                 padx=8, pady=6, relief="sunken").pack(fill="x", side="bottom")

        self.new_image()

    # ---- helpers
    def _read_size(self):
        try:
            w, h = int(self.w_var.get()), int(self.h_var.get())
        except ValueError:
            raise ValueError("Width and height must be integers")
        if not (1 <= w <= MAX_DIM and 1 <= h <= MAX_DIM):
            raise ValueError(f"Width and height must be between 1 and {MAX_DIM}")
        return w, h

    def _ask_save(self, ext, label):
        return filedialog.asksaveasfilename(
            defaultextension=ext, filetypes=[(label, f"*{ext}"), ("All files", "*.*")])

    def _ask_open(self, ext, label):
        return filedialog.askopenfilename(
            filetypes=[(label, f"*{ext}"), ("All files", "*.*")])

    def _run(self, action):
        try:
            action()
        except Exception as e:                       # show any error to the user
            messagebox.showerror("Error", str(e))

    # ---- actions
    def new_image(self):
        def go():
            w, h = self._read_size()
            self.editor.set_image(w, h)
            self.viewer.delete("all")
            self.viewer.w = self.viewer.h = 0
            self.status.set(f"New {w}x{h} image.")
        self._run(go)

    def clear(self):
        self.editor.clear()
        self.status.set("Drawing cleared.")

    def save_raw(self):
        def go():
            path = self._ask_save(".raw", "Raw image")
            if not path:
                return
            size = save_raw(path, self.editor.w, self.editor.h, self.editor.get_pixels())
            self.status.set(f"Saved raw image: {os.path.basename(path)} ({size} bytes)")
        self._run(go)

    def open_raw(self):
        def go():
            path = self._ask_open(".raw", "Raw image")
            if not path:
                return
            w, h, pixels = load_raw(path)
            self.w_var.set(str(w))
            self.h_var.set(str(h))
            self.editor.set_image(w, h, pixels)
            self.status.set(f"Loaded raw image {w}x{h}: {os.path.basename(path)}")
        self._run(go)

    def compress(self):
        def go():
            path = self._ask_save(".rle", "RLE compressed image")
            if not path:
                return
            w, h = self.editor.w, self.editor.h
            pixels = self.editor.get_pixels()
            csize = save_compressed(path, w, h, pixels)
            rsize = HEADER_SIZE + len(pixels)
            ratio = csize / rsize * 100
            gain = 100 - ratio
            self.status.set(
                f"Compressed {os.path.basename(path)}: raw file = {rsize} bytes, "
                f"compressed file = {csize} bytes ({ratio:.1f}% of original, "
                + (f"saved {gain:.1f}%)" if gain >= 0 else f"{-gain:.1f}% LARGER)"))
        self._run(go)

    def open_compressed(self):
        def go():
            path = self._ask_open(".rle", "RLE compressed image")
            if not path:
                return
            w, h, pixels = load_compressed(path)
            self.viewer.set_image(w, h, pixels)
            same = ""
            if (w, h) == (self.editor.w, self.editor.h):
                same = (" | identical to drawing: "
                        + ("YES" if pixels == self.editor.get_pixels() else "no"))
            self.status.set(f"Decompressed {os.path.basename(path)}: {w}x{h}{same}")
        self._run(go)


if __name__ == "__main__":
    App().mainloop()