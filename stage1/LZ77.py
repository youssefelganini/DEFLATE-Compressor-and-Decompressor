# Constants
WINDOW_SIZE = 32768
MIN_MATCH = 3
MAX_MATCH = 258
MAX_CANDIDATES = 64


""" 
--Notice--
the functions deals with bytes as inputs and outputs as stated in the report 
the input/ output from and for the user should be handeld in the main file  
"""

def lz77_compress(Data) -> list:

    Len_Data = len(Data)
    tokens = []

    table = {}
    i= 0

    """
    ---what main loop does---
    scan every position in data and search the previous bytes
    for the longest repeated sequence using the hash table. If a match of 3+
    bytes is found emit a match token, otherwise emit a literal
    token and move one byte forward. Update the hash table after every token.
    """

    while i < Len_Data:

        #fewer than 3 bytes remaining, to build a table we need at least 3 bytes
        if i + MIN_MATCH > Len_Data:
            tokens.append(('literal', Data[i]))
            i +=1
            continue

        key = Data[i: i+3]
        candidates = table.get(key, []) # List of positions matches the same first 3 bytes

        best_length = 0
        best_distance = 0

        for candidate in reversed(candidates[-MAX_CANDIDATES:]): # to get the latest 64 candidates

            distance = i - candidate

            if distance > WINDOW_SIZE:
                break

            #match the same byte byte, to count the length and allow overlapping 
            max_Possible = min(MAX_MATCH, Len_Data - i)
            length = 0
            while length < max_Possible and Data[candidate + length] == Data[i + length]:
                length += 1

            
            if length > best_length:
                best_length   = length
                best_distance = distance

        if best_length >= MIN_MATCH:

            tokens.append(('match', best_length, best_distance))
            #we are skipping the found match, but we need to make a key for each 3 byte for future
            for j in range(i, i + best_length):
                if j + MIN_MATCH <= Len_Data:
                    k = Data[j : j + 3]
                    if k not in table:
                        table[k] = []
                    table[k].append(j)
            i += best_length

        else:

            tokens.append(('literal', Data[i]))

            if key not in table: # for future refrencing, even we emit an literal but we may need the pattern in here for future matches
                table[key] = []
            table[key].append(i)

            i+=1
    return tokens

def lz77_decompress(tokens) -> bytes:

    output = bytearray()

    for token in tokens:

        if token[0] == 'literal':
            output.append(token[1])

        else:
            length = token[1]
            distance = token[2]
            start = len(output) - distance

            for k in range(length):
                output.append(output[start + k])
    return bytes(output)
