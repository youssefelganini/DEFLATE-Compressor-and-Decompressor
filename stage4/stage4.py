length_base = [
    3, 4, 5, 6, 7, 8, 9, 10,
    11, 13, 15, 17,
    19, 23, 27, 31,
    35, 43, 51, 59,
    67, 83, 99, 115,
    131, 163, 195, 227,
    258
]
length_extra = [
    0, 0, 0, 0, 0, 0, 0, 0,
    1, 1, 1, 1,
    2, 2, 2, 2,
    3, 3, 3, 3,
    4, 4, 4, 4,
    5, 5, 5, 5,
    0
]

distance_base = [
    1, 2, 3, 4,
    5, 7,
    9, 13,
    17, 25,
    33, 49,
    65, 97,
    129, 193,
    257, 385,
    513, 769,
    1025, 1537,
    2049, 3073,
    4097, 6145,
    8193, 12289,
    16385, 24577
]
distance_extra = [
    0, 0, 0, 0,
    1, 1,
    2, 2,
    3, 3,
    4, 4,
    5, 5,
    6, 6,
    7, 7,
    8, 8,
    9, 9,
    10, 10,
    11, 11,
    12, 12,
    13, 13
]


def compute_bw(max_len):
    if max_len == 0:
        return 0
    bw = 0
    v = max_len
    while v > 0:
        bw += 1
        v >>= 1
    return bw


def get_lengths_from_symbol_code(symbol_code):
    lengths = []
    for entry in symbol_code:
        if entry is None:
            lengths.append(0)
        else:
            lengths.append(entry[1])
    return lengths


# --- bit writer functions ---

def write_bits(bits, value, num_bits):
    for shift in range(num_bits - 1, -1, -1):
        bits.append((value >> shift) & 1)


def write_bit_string(bits, bit_str, expected_count):
    if expected_count == 0:
        return
    for ch in bit_str:
        bits.append(int(ch))


def bits_to_bytes(bits):
    padded = list(bits)
    while len(padded) % 8 != 0:
        padded.append(0)
    result = bytearray()
    for i in range(0, len(padded), 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | padded[i + j]
        result.append(byte)
    return bytes(result)


# --- bit reader functions ---

def read_bit(data, pos):
    byte_idx = pos[0] // 8
    bit_idx  = 7 - (pos[0] % 8)
    pos[0] += 1
    return (data[byte_idx] >> bit_idx) & 1


def read_bits(data, pos, n):
    value = 0
    for _ in range(n):
        value = (value << 1) | read_bit(data, pos)
    return value


# ---


def build_decoder(lengths):
    count = [0] * 32
    for l in lengths:
        count[l] += 1
    count[0] = 0
    next_code = [0] * 32
    code = 0
    for bits in range(1, 32):
        code = (code + count[bits - 1]) << 1
        next_code[bits] = code
    decoder = {}
    for symbol in range(len(lengths)):
        l = lengths[symbol]
        if l != 0:
            decoder[(next_code[l], l)] = symbol
            next_code[l] += 1
    return decoder


def decode_symbol(data, pos, decoder, max_len):
    code = 0
    for bit_len in range(1, max_len + 1):
        code = (code << 1) | read_bit(data, pos)
        if (code, bit_len) in decoder:
            return decoder[(code, bit_len)]
    raise ValueError(f"No valid Huffman code found within {max_len} bits")


def compress_stage4(event_streams, lit_symbol_code, dist_symbol_code):
    lit_lengths  = get_lengths_from_symbol_code(lit_symbol_code)
    dist_lengths = get_lengths_from_symbol_code(dist_symbol_code)

    lit_bw  = compute_bw(max(lit_lengths))
    dist_bw = compute_bw(max(dist_lengths)) if any(l > 0 for l in dist_lengths) else 0
    bits = []
    write_bits(bits, lit_bw,  4)
    write_bits(bits, dist_bw, 4)
    for l in lit_lengths:
        write_bits(bits, l, lit_bw)
    if dist_bw > 0:
        for l in dist_lengths:
            write_bits(bits, l, dist_bw)
    for event in event_streams:
        if event[0] == "LiteralEvent":
            symbol = event[1]
            code, code_len = lit_symbol_code[symbol]
            write_bits(bits, code, code_len)
        elif event[0] == "MatchEvent":
            len_sym    = event[1]
            len_extra  = event[2]
            dist_sym   = event[3]
            dist_extra = event[4]
            len_extra_count  = length_extra[len_sym - 257]
            dist_extra_count = distance_extra[dist_sym]
            code, code_len = lit_symbol_code[len_sym]
            write_bits(bits, code, code_len)
            write_bit_string(bits, len_extra, len_extra_count)
            code, code_len = dist_symbol_code[dist_sym]
            write_bits(bits, code, code_len)
            write_bit_string(bits, dist_extra, dist_extra_count)
        elif event[0] == "EndEvent":
            code, code_len = lit_symbol_code[256]
            write_bits(bits, code, code_len)
    return bits_to_bytes(bits)


def decompress_stage4(data):
    pos = [0]  # wrapped in a list so subfunctions can update it
    lit_bw  = read_bits(data, pos, 4)
    dist_bw = read_bits(data, pos, 4)
    lit_lengths  = [read_bits(data, pos, lit_bw)  if lit_bw  > 0 else 0 for _ in range(286)]
    dist_lengths = [read_bits(data, pos, dist_bw) if dist_bw > 0 else 0 for _ in range(30)]
    lit_decoder  = build_decoder(lit_lengths)
    dist_decoder = build_decoder(dist_lengths)
    max_lit_len  = max(lit_lengths)  if lit_lengths  else 0
    max_dist_len = max(dist_lengths) if dist_lengths else 0
    output = bytearray()
    while True:
        symbol = decode_symbol(data, pos, lit_decoder, max_lit_len)
        if symbol < 256:
            output.append(symbol)
        elif symbol == 256:
            break
        else:
            idx = symbol - 257
            extra_count  = length_extra[idx]
            extra_val    = read_bits(data, pos, extra_count) if extra_count > 0 else 0
            match_length = length_base[idx] + extra_val
            dist_sym = decode_symbol(data, pos, dist_decoder, max_dist_len)
            dist_extra_count = distance_extra[dist_sym]
            dist_extra_val   = read_bits(data, pos, dist_extra_count) if dist_extra_count > 0 else 0
            match_distance   = distance_base[dist_sym] + dist_extra_val
            start = len(output) - match_distance
            for k in range(match_length):
                output.append(output[start + k])
    return bytes(output)
