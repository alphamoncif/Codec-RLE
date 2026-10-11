"""
codec.py - RLE codec for binary images (pixels are 0x00 or 0xFF).

Compressed stream = sequence of blocks. Each block starts with a 2-byte
header (big-endian, 16 bits):

  RUN block     : bit15 = 1, bits 14..0 = repeat count (>= 3)
                  followed by 1 byte: the repeated pixel
  LITERAL block : bit15 = 0, bits 14..0 = number of pixels
                  followed by that many raw pixel bytes
"""

MAX_COUNT = 0x7FFF      # 15 bits -> 32767 max per block
RUN_FLAG = 0x8000       # bit 15
MIN_RUN = 3             # a run is only worth it from 3 identical pixels


def _emit_run(out: bytearray, pixel: int, count: int) -> None:
    """Write a run, splitting it if it exceeds 15 bits."""
    while count > 0:
        chunk = min(count, MAX_COUNT)
        header = RUN_FLAG | chunk
        out += header.to_bytes(2, "big")
        out.append(pixel)
        count -= chunk


def _emit_literal(out: bytearray, literal: bytearray) -> None:
    """Write the pending literal sequence (if any), then empty it."""
    start = 0
    while start < len(literal):
        chunk = literal[start:start + MAX_COUNT]
        out += len(chunk).to_bytes(2, "big")   # bit15 = 0 automatically
        out += chunk
        start += MAX_COUNT
    literal.clear()


def encode(pixels: bytes) -> bytes:
    """Compress a flat sequence of pixel bytes."""
    out = bytearray()
    literal = bytearray()      # pixels waiting to be written as a literal
    n = len(pixels)
    i = 0
    while i < n:
        # measure the run of identical pixels starting at i
        j = i
        while j < n and pixels[j] == pixels[i]:
            j += 1
        run_len = j - i

        if run_len >= MIN_RUN:
            _emit_literal(out, literal)          # close pending literal first
            _emit_run(out, pixels[i], run_len)
        else:
            literal += pixels[i:j]               # 1 or 2 pixels: keep as literal
        i = j

    _emit_literal(out, literal)                  # don't forget the last one
    return bytes(out)


def decode(data: bytes) -> bytes:
    """Decompress a stream produced by encode()."""
    out = bytearray()
    i = 0
    n = len(data)
    while i < n:
        if i + 2 > n:
            raise ValueError("Truncated header")
        header = int.from_bytes(data[i:i + 2], "big")
        i += 2
        count = header & MAX_COUNT

        if header & RUN_FLAG:                    # RUN block
            if i >= n:
                raise ValueError("Truncated run block")
            out += bytes([data[i]]) * count
            i += 1
        else:                                    # LITERAL block
            if i + count > n:
                raise ValueError("Truncated literal block")
            out += data[i:i + count]
            i += count
    return bytes(out)


def analyze(data: bytes) -> list:
    """Parse a compressed stream into a list of blocks (for display/stats).

    Each block is a dict:
      offset  : position of the block in the stream
      type    : "RUN" or "LITERAL"
      header  : the 2 header bytes
      count   : number of pixels the block represents
      size    : number of bytes the block occupies in the stream
      pixel   : (RUN only) the repeated pixel value
      content : (LITERAL only) the raw pixel bytes
    """
    blocks = []
    i = 0
    n = len(data)
    while i < n:
        if i + 2 > n:
            raise ValueError("Truncated header")
        start = i
        header = data[i:i + 2]
        value = int.from_bytes(header, "big")
        i += 2
        count = value & MAX_COUNT
        if value & RUN_FLAG:
            if i >= n:
                raise ValueError("Truncated run block")
            blocks.append({"offset": start, "type": "RUN", "header": header,
                           "count": count, "size": 3, "pixel": data[i]})
            i += 1
        else:
            if i + count > n:
                raise ValueError("Truncated literal block")
            blocks.append({"offset": start, "type": "LITERAL", "header": header,
                           "count": count, "size": 2 + count,
                           "content": bytes(data[i:i + count])})
            i += count
    return blocks
