# Simplified DEFLATE Compressor & Decompressor

A Python implementation of a simplified DEFLATE-inspired file compressor and decompressor, built as part of an Information Theory course project. The pipeline follows the core ideas behind the real DEFLATE algorithm used in ZIP, PNG, and HTTP compression.

---

## Table of Contents

- [Overview](#overview)
- [Pipeline](#pipeline)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [Stage 1 — LZ77 Pattern Detection](#stage-1--lz77-pattern-detection)
- [Stage 2 — DEFLATE Symbols and Extra Bits](#stage-2--deflate-symbols-and-extra-bits)
- [Stage 3 — Canonical Huffman Coding](#stage-3--canonical-huffman-coding)
- [Stage 4 — Custom Header and Payload](#stage-4--custom-header-and-payload)
- [Correctness Guarantee](#correctness-guarantee)
- [Information Theory Background](#information-theory-background)

---

## Overview

This project implements a lossless file compressor inspired by DEFLATE. It is not a full `.gz` implementation — there is no GZIP header, CRC32, or official DEFLATE block structure. The only requirement is:

```
decompress(compress(data)) == data   byte for byte
```

The compressor works on any file as a raw byte stream — text files, binary files, images, anything.

---

## Pipeline

```
COMPRESS:
  Input File
      │
      ▼
  Stage 1 — LZ77           finds repeated byte sequences → tokens
      │
      ▼
  Stage 2 — DEFLATE Symbols converts tokens → symbols + extra bits
      │
      ▼
  Stage 3 — Huffman Coding  assigns short codes to frequent symbols
      │
      ▼
  Stage 4 — File Writer     writes header + payload → .sdfl file


DECOMPRESS:
  .sdfl file
      │
      ▼
  Stage 4 — Header Reader   reads Huffman code lengths
      │
      ▼
  Stage 3 — Huffman Decoder reconstructs canonical codes
      │
      ▼
  Stage 2 — Symbol Decoder  reads length/distance symbols + extra bits
      │
      ▼
  Stage 1 — LZ77 Copy       copies back-references → original bytes
      │
      ▼
  Original File
```

---

## Project Structure

```
.
├── LZ77.py               Stage 1 — LZ77 compressor
├── deflate_symboles.py   Stage 2 — DEFLATE symbol encoding
├── huffman.py            Stage 3 — Huffman tree + canonical codes
├── stage4.py             Stage 4 — bit-level file format + full decompressor
├── main.py               Entry point — CLI interface
└── test_LZ77.py          Unit tests for Stage 1
```

---

## Usage

**Compress a file:**
```bash
python main.py -c filename
```
Creates `filename.sdfl` in the same directory.

**Decompress a file:**
```bash
python main.py -d filename.sdfl
```
Recreates the original file by stripping the `.sdfl` extension.

**Example:**
```bash
python main.py -c report.txt
# creates report.txt.sdfl

python main.py -d report.txt.sdfl
# recreates report.txt
```

---

## Stage 1 — LZ77 Pattern Detection

**File:** `LZ77.py`

### What it does

LZ77 scans the input from left to right looking for repeated byte sequences. Instead of writing the same bytes again, it writes a back-reference: *"go back N bytes and copy M bytes."* This back-reference is always shorter than the bytes it replaces, so the data shrinks.

### Token types

The output is a list of two token types represented as plain tuples:

```python
('literal', byte)             # output this single byte as-is
('match',   length, distance) # go back `distance` bytes, copy `length` bytes
```

**Example:** `"abcabcabcabc"` → 12 bytes becomes 4 tokens:

```python
('literal', 97)   # 'a'
('literal', 98)   # 'b'
('literal', 99)   # 'c'
('match', 9, 3)   # go back 3, copy 9  →  saves 9 bytes
```

### Constants

```python
WINDOW_SIZE    = 32768   # how far back we look for matches (32 KB)
MIN_MATCH      = 3       # minimum match length worth encoding
MAX_MATCH      = 258     # maximum match length (DEFLATE table limit)
MAX_CANDIDATES = 64      # max past positions checked per step
```

### Hash table speedup

A naive search checks all 32,768 previous positions at every step — too slow for large files. Instead we use a hash table:

```python
table[key] = deque(maxlen=MAX_CANDIDATES)
# key = first 3 bytes at that position
```

A valid match of length ≥ 3 **must** start with the same 3 bytes as the current position. So we only check positions that share those 3 bytes — at most 64 candidates instead of 32,768.

We use `collections.deque(maxlen=64)` which automatically drops the oldest entry when full, so no manual slicing is needed.

### Match selection rules

- Search only the previous 32,768 bytes
- Find the longest match — tie-break by smallest distance
- Only emit a match if `length >= 3`, otherwise emit a literal
- Cap match length at 258

### Overlapping matches

LZ77 allows a match to overlap with itself. For example, `"aaaaaaaaaa"` compresses as:

```python
('literal', 97)     # one 'a'
('match', 9, 1)     # go back 1, copy 9  →  each new 'a' is immediately available
```

The decompressor copies **one byte at a time** — not with a slice — so each newly written byte is immediately available for the rest of the same copy.

```python
# correct — handles overlapping
for k in range(length):
    output.append(output[start + k])

# wrong — slice is a frozen snapshot, misses overlapping bytes
output += output[start : start + length]
```

### Updating the hash table after a match

When a match of length `L` is emitted, we skip `L` positions at once. Those skipped positions are never visited by the main loop, but future searches might need them as candidates. So we insert all positions `i` through `i+L-1` into the table immediately after emitting a match.

---

## Stage 2 — DEFLATE Symbols and Extra Bits

**File:** `deflate_symboles.py`

### What it does

Stage 1 produces raw `('match', length, distance)` tokens. Huffman coding in Stage 3 requires a **fixed-size alphabet**. Stage 2 converts every token into a format that fits that alphabet.

### The problem with raw lengths and distances

- Lengths range from 3 to 258 — that is 256 possible values
- Distances range from 1 to 32,768 — that is 32,768 possible values

Feeding these raw values into Huffman would require a 32,768-symbol distance alphabet, making the Huffman table enormous. Stage 2 solves this by grouping nearby values into **ranges**, each represented by a single symbol plus a few raw **extra bits** that identify the exact value within the range.

### Length encoding

Lengths 3–258 are mapped to 29 symbols (257–285) using a lookup table:

```
length 9  →  symbol 263,  0 extra bits  (exact value, no extra bits needed)
length 20 →  symbol 269,  2 extra bits  "01"  (range 19-22, offset = 20-19 = 1)
length 258→  symbol 285,  0 extra bits
```

### Distance encoding

Distances 1–32,768 are mapped to 30 symbols (0–29):

```
distance 3 →  symbol 2,  0 extra bits
distance 6 →  symbol 4,  1 extra bit  "1"  (range 5-6, offset = 6-5 = 1)
```

### Event stream output

```python
('literal', 97)           →  ("LiteralEvent", 97)
('match', 9, 3)           →  ("MatchEvent", 263, "", 2, "")
('match', 20, 6)          →  ("MatchEvent", 269, "01", 4, "1")
                              # always ends with:
                              ("EndEvent", 256)
```

The `EndEvent(256)` tells the decompressor exactly where the payload ends.

### Why this matters

By grouping 32,768 distance values into just 30 symbols, Stage 2 keeps the Huffman alphabet small. Frequent symbols (like small distances) end up with short Huffman codes. The extra bits are written raw — they are too spread out to benefit from Huffman anyway.

---

## Stage 3 — Canonical Huffman Coding

**File:** `huffman.py`

### What it does

Stage 3 builds Huffman codes for the two alphabets produced by Stage 2:

- **Literal/length alphabet:** 286 symbols (0–255 literals + 256 end + 257–285 length symbols)
- **Distance alphabet:** 30 symbols (0–29)

Frequent symbols get short codes; rare symbols get long codes. This removes statistical redundancy from the symbol stream.

### Frequency counting

```python
def count_frequencies(event_streams):
    # LiteralEvent → increment lit_freq[symbol]
    # MatchEvent   → increment lit_freq[length_symbol] and dist_freq[distance_symbol]
    # EndEvent     → increment lit_freq[256]
    # extra bits are NOT counted — they are raw bits, not symbols
```

### Building the Huffman tree

Uses Python's `heapq` (min-heap priority queue):

1. Push every symbol with frequency > 0 as a leaf node
2. Repeatedly pop the two lowest-frequency nodes, merge them into a parent, push back
3. Tie-breaking: when two nodes have equal frequency, prefer the one with the smaller symbol value — this makes the tree deterministic

```python
heapq.heappush(heap, (freq1 + freq2, merged_min, (sym1, sym2)))
#                      ↑ combined freq  ↑ min symbol for tiebreak
```

4. Walk the final tree recursively — depth of each leaf = code length for that symbol

### Regular Huffman vs Canonical Huffman

Regular Huffman gives valid codes but they are not unique — two implementations may produce different codes for the same lengths. The decompressor would need the full tree stored in the file.

Canonical Huffman solves this: given only the **code lengths**, there is exactly one valid set of codes. The algorithm:

1. Count how many symbols have each length
2. Compute the first code for each length by left-shifting
3. Assign codes to symbols in increasing symbol order within each length

```python
code = 0
for bits in range(1, 16):
    code = (code + count[bits - 1]) << 1   # move to next tree level
    next_code[bits] = code                  # first code for this length
```

**Example:**

```
Symbol lengths:  99→2,  256→2,  263→2,  97→3,  98→3

length 2 codes start at 00:
  99  → 00
  256 → 01
  263 → 10

length 3 codes start at 110:
  97  → 110
  98  → 111
```

The decompressor can reconstruct these exact codes from just the lengths — no tree needed.

---

## Stage 4 — Custom Header and Payload

**File:** `stage4.py`

### File format

The `.sdfl` file has this exact layout:

```
┌─────────────┬──────────────────────────────────────────────────────┐
│ Field       │ Description                                          │
├─────────────┼──────────────────────────────────────────────────────┤
│ LIT_BW      │ 4 bits — bit-width of each literal/length code length│
│ DIST_BW     │ 4 bits — bit-width of each distance code length      │
│ LIT_TABLE   │ 286 × LIT_BW bits — code lengths for symbols 0–285  │
│ DIST_TABLE  │ 30 × DIST_BW bits  — code lengths for symbols 0–29  │
│ PAYLOAD     │ Huffman-coded symbols + raw extra bits               │
└─────────────┴──────────────────────────────────────────────────────┘
```

All bits are written **MSB first**. The last byte is zero-padded to a full 8 bits.

### Bit-width calculation

```python
def compute_bw(max_len):
    # how many bits needed to store values 0..max_len
    # e.g. max_len=7  →  bw=3  (binary 111)
    #      max_len=15 →  bw=4  (binary 1111)
```

### Payload writing order

For each event in the stream:

```
LiteralEvent(s)                  →  Huffman(s)
MatchEvent(len_sym, len_extra,   →  Huffman(len_sym)
           dist_sym, dist_extra)    len_extra (raw bits)
                                    Huffman(dist_sym)
                                    dist_extra (raw bits)
EndEvent(256)                    →  Huffman(256)
```

### Decompression

`decompress_stage4` reverses all four stages in a single function:

```
1. Read LIT_BW, DIST_BW from header
2. Read 286 lit lengths, 30 dist lengths
3. Rebuild canonical Huffman decoder from lengths alone
4. Loop:
     decode one literal/length symbol
     if symbol 0-255  → append byte to output
     if symbol 256    → stop (EndEvent)
     if symbol 257+   → read length extra bits → actual length
                        decode distance symbol
                        read distance extra bits → actual distance
                        copy bytes from output (byte-by-byte for overlapping)
```

This means `decompress_stage4` is the **complete decompressor** — it reverses Stage 4 (header), Stage 3 (Huffman), Stage 2 (symbols+extra bits), and Stage 1 (LZ77 copy) all in one pass.

---

## Correctness Guarantee

The project satisfies the required correctness property:

```python
decompress_stage4(compress_stage4(...)) == original_data
```

for all inputs including:
- Empty files
- Single bytes
- Binary files (all 256 byte values)
- Files with long repetitive patterns
- Files with no repetition (random data)

---

## Information Theory Background

This project is a practical implementation of two fundamental ideas from Shannon's information theory:

**Source Coding Theorem:** Data cannot be compressed below its entropy `H(X) = -Σ p(x) log₂ p(x)` without losing information. This compressor is lossless — it respects this bound.

**Redundancy removal:** The pipeline attacks redundancy from two angles:
- **LZ77 (Stage 1):** removes structural redundancy — repeated byte sequences
- **Huffman (Stage 3):** removes statistical redundancy — frequent symbols get shorter codes

Together they approach the theoretical entropy limit much more closely than either could alone. This is why the same combination (LZ77 + Huffman = DEFLATE) is used in ZIP, PNG, gzip, and HTTP compression.

**LZ77 as a universal code:** Ziv and Lempel proved that LZ77 achieves the entropy rate of any stationary ergodic source asymptotically — without needing to know the source statistics in advance. The sliding window acts as a self-built dictionary learned from the data itself.
