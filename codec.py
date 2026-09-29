"""
codec.py - Run-Length Encoding (RLE) codec for binary image pixels.

Format:
    Each block has a 2-byte (16-bit, big-endian) header:
      - Bit 15 = 1 (0x8000 | count): RUN block.
        Followed by 1 byte representing the repeated pixel value.
        Count can be from 1 to 32767.
      - Bit 15 = 0 (0x0000 | count): LITERAL block.
        Followed by `count` bytes of raw pixel data.
        Count can be from 1 to 32767.
"""

MAX_COUNT = 32767  # 0x7FFF (15 bits)
RUN_FLAG = 0x8000
MIN_RUN = 3


def encode(pixels: bytes) -> bytes:
    """Encode raw pixel bytes into an RLE stream."""
    if not pixels:
        return b""

    out = bytearray()
    literal = bytearray()

    def flush_literal():
        nonlocal literal
        if not literal:
            return
        offset = 0
        while offset < len(literal):
            chunk = literal[offset : offset + MAX_COUNT]
            out.extend(len(chunk).to_bytes(2, "big"))
            out.extend(chunk)
            offset += len(chunk)
        literal = bytearray()

    i = 0
    n = len(pixels)
    while i < n:
        # Check length of identical run starting at i
        run_len = 1
        while i + run_len < n and pixels[i + run_len] == pixels[i] and run_len < MAX_COUNT:
            run_len += 1

        if run_len >= MIN_RUN:
            flush_literal()
            # Emit run block
            header = RUN_FLAG | run_len
            out.extend(header.to_bytes(2, "big"))
            out.append(pixels[i])
            i += run_len
        else:
            literal.append(pixels[i])
            if len(literal) == MAX_COUNT:
                flush_literal()
            i += 1

    flush_literal()
    return bytes(out)


def decode(data: bytes) -> bytes:
    """Decode an RLE stream back into raw pixel bytes."""
    if not data:
        return b""

    out = bytearray()
    i = 0
    n = len(data)

    while i < n:
        if i + 2 > n:
            raise ValueError("Truncated header in RLE stream")
        header = int.from_bytes(data[i : i + 2], "big")
        i += 2

        is_run = bool(header & RUN_FLAG)
        count = header & MAX_COUNT

        if count == 0:
            continue

        if is_run:
            if i >= n:
                raise ValueError("Unexpected end of stream: expected run pixel byte")
            pixel = data[i]
            i += 1
            out.extend([pixel] * count)
        else:
            if i + count > n:
                raise ValueError("Unexpected end of stream: truncated literal data")
            out.extend(data[i : i + count])
            i += count

    return bytes(out)