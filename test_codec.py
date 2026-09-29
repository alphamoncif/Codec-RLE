import random
from codec import encode, decode

W, B = 0xFF, 0x00


def test_example_from_lesson():
    pixels = bytes([W, W, W, W,  B, W, B, B,  W, W, W])
    expected = bytes.fromhex("8004FF" "000400FF0000" "8003FF")
    assert encode(pixels) == expected
    assert decode(expected) == pixels


def test_edge_cases():
    assert encode(b"") == b""
    assert decode(b"") == b""
    for px in (bytes([W]), bytes([B, W]), bytes([W] * 3), bytes([B] * 2)):
        assert decode(encode(px)) == px


def test_long_run_is_split():
    pixels = bytes([W]) * 70000          # > 2 * 32767
    enc = encode(pixels)
    assert len(enc) == 3 * 3             # 3 run blocks of 3 bytes each
    assert decode(enc) == pixels


def test_long_literal_is_split():
    pixels = bytes([W, B] * 20000)       # alternating -> pure literal, 40000 px
    assert decode(encode(pixels)) == pixels


def test_random_roundtrip():
    random.seed(1)
    for _ in range(300):
        size = random.randint(0, 500)
        p = random.choice([0.1, 0.5, 0.9])
        pixels = bytes(W if random.random() < p else B for _ in range(size))
        assert decode(encode(pixels)) == pixels


if __name__ == "__main__":
    test_example_from_lesson()
    test_edge_cases()
    test_long_run_is_split()
    test_long_literal_is_split()
    test_random_roundtrip()
    print("All tests passed")