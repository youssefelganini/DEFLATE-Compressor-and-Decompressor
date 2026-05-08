# =============================================================================
# Unit tests for lz77_compress and lz77_decompress
# =============================================================================

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from LZ77 import lz77_compress, lz77_decompress

passed = 0
failed = 0

def divider():
    print("=" * 60)

def section(title):
    print()
    divider()
    print(f"  {title}")
    divider()

def check(test_name, condition, input_val, output_val, expected_val, details=""):
    global passed, failed
    status = "PASS" if condition else "FAIL"
    if condition:
        passed += 1
    else:
        failed += 1
    print(f"\n  Test : {test_name}")
    print(f"  Input    : {input_val}")
    print(f"  Output   : {output_val}")
    print(f"  Expected : {expected_val}")
    print(f"  Result   : [{status}]")
    if not condition and details:
        print(f"  Details  : {details}")


# =============================================================================
# SECTION 1: tokens store integers not characters
# =============================================================================
section("Section 1: Tokens Store Integers, Not Characters")

data   = b"abc"
tokens = lz77_compress(data)

check(
    test_name = "literal value of 'a' is integer 97",
    condition = tokens[0][1] == 97,
    input_val = "b'abc'  →  compress  →  tokens[0]",
    output_val = tokens[0],
    expected_val = ('literal', 97),
)

check(
    test_name = "literal value of 'b' is integer 98",
    condition = tokens[1][1] == 98,
    input_val = "b'abc'  →  compress  →  tokens[1]",
    output_val = tokens[1],
    expected_val = ('literal', 98),
)

check(
    test_name = "literal value of 'c' is integer 99",
    condition = tokens[2][1] == 99,
    input_val = "b'abc'  →  compress  →  tokens[2]",
    output_val = tokens[2],
    expected_val = ('literal', 99),
)


# =============================================================================
# SECTION 2: spec example abcabcabcabc
# =============================================================================
section("Section 2: Spec Example  'abcabcabcabc'")

data   = b"abcabcabcabc"
tokens = lz77_compress(data)

check(
    test_name = "produces exactly 4 tokens",
    condition = len(tokens) == 4,
    input_val = data,
    output_val = f"{len(tokens)} tokens  →  {tokens}",
    expected_val = "4 tokens",
)

check(
    test_name = "token 0 is Literal(97)",
    condition = tokens[0] == ('literal', 97),
    input_val = data,
    output_val = tokens[0],
    expected_val = ('literal', 97),
)

check(
    test_name = "token 1 is Literal(98)",
    condition = tokens[1] == ('literal', 98),
    input_val = data,
    output_val = tokens[1],
    expected_val = ('literal', 98),
)

check(
    test_name = "token 2 is Literal(99)",
    condition = tokens[2] == ('literal', 99),
    input_val = data,
    output_val = tokens[2],
    expected_val = ('literal', 99),
)

check(
    test_name = "token 3 is Match(length=9, distance=3)",
    condition = tokens[3] == ('match', 9, 3),
    input_val = data,
    output_val = tokens[3],
    expected_val = ('match', 9, 3),
)

reconstructed = lz77_decompress(tokens)
check(
    test_name = "roundtrip restores original bytes",
    condition = reconstructed == data,
    input_val = f"tokens = {tokens}",
    output_val = reconstructed,
    expected_val = data,
)


# =============================================================================
# SECTION 3: overlapping match aaaaaaaaaa
# =============================================================================
section("Section 3: Overlapping Match  'aaaaaaaaaa'")

data   = b"aaaaaaaaaa"
tokens = lz77_compress(data)

check(
    test_name = "produces exactly 2 tokens",
    condition = len(tokens) == 2,
    input_val = data,
    output_val = f"{len(tokens)} tokens  →  {tokens}",
    expected_val = "2 tokens",
)

check(
    test_name = "token 0 is Literal(97)",
    condition = tokens[0] == ('literal', 97),
    input_val = data,
    output_val = tokens[0],
    expected_val = ('literal', 97),
)

check(
    test_name = "token 1 is Match(length=9, distance=1)",
    condition = tokens[1] == ('match', 9, 1),
    input_val = data,
    output_val = tokens[1],
    expected_val = ('match', 9, 1),
)

reconstructed = lz77_decompress(tokens)
check(
    test_name = "roundtrip restores original bytes",
    condition = reconstructed == data,
    input_val = f"tokens = {tokens}",
    output_val = reconstructed,
    expected_val = data,
)


# =============================================================================
# SECTION 4: no repetition, all literals
# =============================================================================
section("Section 4: No Repetition — All Unique Bytes")

data   = bytes(range(10))
tokens = lz77_compress(data)

check(
    test_name = "every token is a literal",
    condition = all(t[0] == 'literal' for t in tokens),
    input_val = data,
    output_val = tokens,
    expected_val = "all tokens are ('literal', ...)",
)

check(
    test_name = "number of tokens equals number of bytes",
    condition = len(tokens) == len(data),
    input_val = data,
    output_val = f"{len(tokens)} tokens",
    expected_val = f"{len(data)} tokens",
)

reconstructed = lz77_decompress(tokens)
check(
    test_name = "roundtrip restores original bytes",
    condition = reconstructed == data,
    input_val = f"tokens = {tokens}",
    output_val = reconstructed,
    expected_val = data,
)


# =============================================================================
# SECTION 5: edge cases
# =============================================================================
section("Section 5: Edge Cases")

# empty input
tokens = lz77_compress(b"")
check(
    test_name = "empty input produces empty token list",
    condition = tokens == [],
    input_val = b"",
    output_val = tokens,
    expected_val = [],
)

result = lz77_decompress([])
check(
    test_name = "empty token list decompresses to empty bytes",
    condition = result == b"",
    input_val = [],
    output_val = result,
    expected_val = b"",
)

# single byte
tokens = lz77_compress(b"Z")
check(
    test_name = "single byte produces one literal with integer 90",
    condition = tokens == [('literal', 90)],
    input_val = b"Z",
    output_val = tokens,
    expected_val = [('literal', 90)],
)

# two bytes — too short for a match
tokens = lz77_compress(b"ab")
check(
    test_name = "two bytes produce two literals",
    condition = len(tokens) == 2 and all(t[0] == 'literal' for t in tokens),
    input_val = b"ab",
    output_val = tokens,
    expected_val = [('literal', 97), ('literal', 98)],
)


# =============================================================================
# SECTION 6: match constraints from the spec
# =============================================================================
section("Section 6: Match Constraints (Spec Rules)")

data   = b"abcabcabcabc" * 10
tokens = lz77_compress(data)
matches = [t for t in tokens if t[0] == 'match']

check(
    test_name = "no match has length less than MIN_MATCH (3)",
    condition = all(t[1] >= 3 for t in matches),
    input_val = f"b'abcabc...' x10  ({len(data)} bytes)",
    output_val = f"{len(matches)} match tokens, min length = {min(t[1] for t in matches) if matches else 'N/A'}",
    expected_val = "all match lengths >= 3",
)

check(
    test_name = "no match has length greater than MAX_MATCH (258)",
    condition = all(t[1] <= 258 for t in matches),
    input_val = f"b'abcabc...' x10  ({len(data)} bytes)",
    output_val = f"max length found = {max(t[1] for t in matches) if matches else 'N/A'}",
    expected_val = "all match lengths <= 258",
)

check(
    test_name = "no match has distance greater than WINDOW_SIZE (32768)",
    condition = all(t[2] <= 32768 for t in matches),
    input_val = f"b'abcabc...' x10  ({len(data)} bytes)",
    output_val = f"max distance found = {max(t[2] for t in matches) if matches else 'N/A'}",
    expected_val = "all distances <= 32768",
)

reconstructed = lz77_decompress(tokens)
check(
    test_name = "roundtrip restores original bytes",
    condition = reconstructed == data,
    input_val = f"{len(data)} bytes  →  {len(tokens)} tokens  →  decompress",
    output_val = f"{len(reconstructed)} bytes, matches original: {reconstructed == data}",
    expected_val = f"{len(data)} bytes identical to input",
)


# =============================================================================
# SECTION 7: longer realistic strings
# =============================================================================
section("Section 7: Longer Realistic Strings")

sentences = [
    b"the cat sat on the mat and the cat sat on the hat",
    b"hello world hello world hello world",
    b"aababcabcdabcde",
    b"compression is the art of finding repeated patterns",
]

for s in sentences:
    tokens        = lz77_compress(s)
    result        = lz77_decompress(tokens)
    n_literals    = sum(1 for t in tokens if t[0] == 'literal')
    n_matches     = sum(1 for t in tokens if t[0] == 'match')
    check(
        test_name = f"roundtrip: '{s.decode()[:40]}'",
        condition = result == s,
        input_val = f"{s}  ({len(s)} bytes)",
        output_val = f"{len(tokens)} tokens  ({n_literals} literals, {n_matches} matches)  →  {result}",
        expected_val = s,
    )


# =============================================================================
# SECTION 8: manual decompressor tokens
# =============================================================================
section("Section 8: Manual Decompressor Token Tests")

result = lz77_decompress([('literal', 97), ('literal', 98), ('literal', 99)])
check(
    test_name = "three literals produce b'abc'",
    condition = result == b"abc",
    input_val = [('literal', 97), ('literal', 98), ('literal', 99)],
    output_val = result,
    expected_val = b"abc",
)

result = lz77_decompress([('literal', 97), ('match', 9, 1)])
check(
    test_name = "overlapping match produces b'aaaaaaaaaa'",
    condition = result == b"aaaaaaaaaa",
    input_val = [('literal', 97), ('match', 9, 1)],
    output_val = result,
    expected_val = b"aaaaaaaaaa",
)

result = lz77_decompress([
    ('literal', 97), ('literal', 98), ('literal', 99), ('match', 9, 3)
])
check(
    test_name = "spec example tokens produce b'abcabcabcabc'",
    condition = result == b"abcabcabcabc",
    input_val = [('literal',97), ('literal',98), ('literal',99), ('match',9,3)],
    output_val = result,
    expected_val = b"abcabcabcabc",
)


# =============================================================================
# Summary
# =============================================================================
total = passed + failed
print()
divider()
print(f"  FINAL RESULTS:  {passed}/{total} tests passed")
divider()
if failed == 0:
    print("  All tests passed!")
else:
    print(f"  {failed} test(s) FAILED — check output above")
divider()
