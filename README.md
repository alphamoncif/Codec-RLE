<div align="center">

# 🗜️ Codec-RLE: Binary Image Compression & Interactive Studio

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg?style=for-the-badge)](https://www.python.org/)
[![Architecture](https://img.shields.io/badge/GUI-Tkinter-informational.svg?style=for-the-badge)](https://docs.python.org/3/library/tkinter.html)
[![License](https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg?style=for-the-badge)](test_codec.py)

**A high-performance Run-Length Encoding (RLE) codec and dual-canvas pixel editor designed for binary bitmap graphics.**

[Key Features](#-key-features) • [Binary Format Protocol](#-binary-format-specification) • [Getting Started](#-getting-started) • [GUI Guide](#-interactive-gui-controls) • [Testing](#-test-suite--validation)

---

</div>

## 📌 Overview

**Codec-RLE** is a complete end-to-end lossless image compression suite built from scratch in Python. It couples a bit-packed **Run-Length Encoding (RLE)** engine with an interactive **Tkinter pixel art studio**, allowing you to draw binary images (black & white), inspect compression ratios in real time, and verify side-by-side lossless decompression instantly.

```
       [ Drawing Canvas ]                          [ Decompressed View ]
   ┌────────────────────────┐                  ┌────────────────────────┐
   │ ■ ■ ■ ■ □ ■ □ □ ■ ■ ■  │                  │ ■ ■ ■ ■ □ ■ □ □ ■ ■ ■  │
   │ ■ ■ ■ ■ □ ■ □ □ ■ ■ ■  │                  │ ■ ■ ■ ■ □ ■ □ □ ■ ■ ■  │
   │ □ □ □ □ □ □ □ □ □ □ □  │                  │ □ □ □ □ □ □ □ □ □ □ □  │
   └───────────┬────────────┘                  └───────────▲────────────┘
               │                                           │
               ▼                                           │
      [ codec.encode() ]                          [ codec.decode() ]
               │                                           │
               └─────────►  .rle Binary Stream  ───────────┘
                           (16-bit Header + Blocks)
```

---

## ✨ Key Features

- 🎨 **Interactive Dual-Canvas Studio**: Draw on an editable grid (up to 200×200 resolution) and see real-time side-by-side decompressed results.
- ⚡ **Optimized Hybrid Encoding**: Intelligently switches between **Run Blocks** and **Literal Blocks** to prevent data inflation on high-frequency noise.
- 📐 **Custom 16-Bit Block Protocol**: Supports run lengths and literal spans up to **32,767 pixels** per block with automatic stream chunking.
- 📊 **Real-time Compression Metrics**: Displays file size differences, compression ratio (%), and net bandwidth saved.
- 💾 **Dual File I/O Format**: Supports exporting and importing uncompressed `.raw` images and compressed `.rle` archives.
- 🛡️ **Zero External Dependencies**: Standard Python standard library only (`tkinter`, `random`, `os`).

---

## 🔬 Binary Format Specification

Every `.rle` and `.raw` file begins with a fixed **4-byte Big-Endian Header** followed by the payload:

### 1. File Header (4 Bytes)
```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          WIDTH (16-bit)       |        HEIGHT (16-bit)        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### 2. Compressed Stream Blocks (`.rle`)
The compressed payload consists of variable-length blocks. Each block begins with a **16-bit control descriptor**:

```
 0                   1
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|F|      COUNT (15-bit)         |  --> F = 1: RUN BLOCK | F = 0: LITERAL BLOCK
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

| Block Type | Flag Bit (Bit 15) | Count Range | Payload Structure | Total Size |
| :--- | :---: | :---: | :--- | :---: |
| **RUN Block** | `1` (`0x8000`) | $1 \le N \le 32767$ | 1 byte: pixel value (`0x00` or `0xFF`) | **3 Bytes** |
| **LITERAL Block** | `0` (`0x0000`) | $1 \le N \le 32767$ | $N$ bytes: raw pixel stream | **$2 + N$ Bytes** |

#### Why Hybrid RLE?
Encoding short runs ($< 3$ pixels) as run blocks adds 3 bytes of overhead, which causes negative compression. Our encoder applies an adaptive heuristic:
- Consecutive runs of **$\ge 3$ identical pixels** are packed into **Run Blocks** (`0x8000 | count` + pixel byte).
- Dispersed pixels or runs $< 3$ are coalesced into **Literal Blocks** (`0x0000 | count` + raw bytes).

---

## 🔄 Compression Pipeline

```mermaid
flowchart TD
    A[Raw Pixel Buffer] --> B{Scan Next Run}
    B -->|Run Length >= 3| C[Flush Pending Literals]
    C --> D[Emit RUN Block: 0x8000 | Len + Pixel]
    D --> B
    B -->|Run Length < 3| E[Append to Literal Buffer]
    E --> F{Literal Buffer == 32767?}
    F -->|Yes| G[Flush LITERAL Block: 0x0000 | Len + Data]
    G --> B
    F -->|No| B
    B -->|End of Pixels| H[Flush Remaining Literals]
    H --> I[Output Compressed .rle Stream]
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher installed on your system.
- Tkinter (included by default on Windows/macOS; on Linux: `sudo apt install python3-tk`).

### Installation
Clone this repository to your local machine:
```bash
git clone https://github.com/alphamoncif/Codec-RLE.git
cd Codec-RLE
```

### Launch the Application
Run the graphical studio:
```bash
python rle_app.py
```

---

## 🎮 Interactive GUI Controls

| Action | Control | Description |
| :--- | :--- | :--- |
| **Draw Black** | Left Click / Drag | Paints selected cell(s) black (`0x00`) |
| **Erase (White)** | Right Click / Drag | Restores selected cell(s) to white (`0xFF`) |
| **New Image** | Click `New` | Resets canvas to dimensions in Width/Height inputs |
| **Clear** | Click `Clear` | Resets current drawing to all-white |
| **Compress & Save** | Click `Compress & save` | Encodes active drawing and exports `.rle` file |
| **Open Compressed** | Click `Open compressed` | Loads & decodes `.rle` file into viewer canvas |
| **Save / Open Raw** | Click `Save raw` / `Open raw` | Exports or imports uncompressed `.raw` pixel data |

---

## 🧪 Test Suite & Validation

The test suite thoroughly verifies the codec against edge cases, boundary thresholds, and fuzzing:

```bash
python test_codec.py
```

### Test Coverage Highlights:
- ✅ **Lesson Benchmark**: Verifies exact byte-for-byte alignment with standard test vectors:
  $$\text{pixels} = [W, W, W, W, B, W, B, B, W, W, W] \longrightarrow \texttt{8004FF 000400FF0000 8003FF}$$
- ✅ **Boundary & Edge Cases**: Empty stream (`b""`), single pixels, alternating doublets.
- ✅ **Chunk Splitting**: Handles sequences $> 32,767$ pixels by transparently partitioning them into multiple 15-bit blocks.
- ✅ **Random Fuzz Roundtrips**: 300 automated randomized binary streams at multiple density distributions ($p = 0.1, 0.5, 0.9$) verifying $100\%$ lossless roundtrips.

---

## 📂 Project Architecture

```
Codec-RLE/
├── codec.py          # Core RLE encode/decode compression engine
├── rle_app.py        # Tkinter visual drawing studio & file manager
├── test_codec.py     # Comprehensive unit tests & roundtrip validator
├── .gitignore        # Ignores bytecache and IDE configuration files
└── README.md         # Documentation and project manual
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
