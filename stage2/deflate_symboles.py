
def len_encoding(length):
    """
    Parmeter -> int.
    Returns -> tuple(length_symbol -> int, extra_bits -> str)
    This funcation to encode the len by finding  where the len is 
    located through the formula in the sheet and to find the extra bits.
    """
    length_base = [
    3, 4, 5, 6, 7, 8, 9, 10,
    11, 13, 15, 17,
    19, 23, 27, 31,
    35, 43, 51, 59,
    67, 83, 99, 115 ,
    131 , 163 , 195 , 227 ,
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
    length_symbol = 257
    extra_value = 0
    
    for i in range(len(length_base)):

        if(length_base[i] <= length and 
            length <= length_base[i] + 2 ** length_extra[i] - 1):

            length_symbol = length_symbol + i
            
            extra_value = length - length_base[i]
            extra_count = length_extra[i]
            extra_bits = f"{extra_value:0{extra_count}b}"
            
            break


    return length_symbol, extra_bits


def distance_encoding(distance):
    """
    Parmeter -> int.
    Returns -> tuple(distance_symbol -> int, extra_bits -> str)
    This funcation to encode the distance by finding  where the distance is 
    located through the formula in the sheet and to find the extra bits.
    """

    distance_base = [
    1, 2, 3, 4,
    5, 7,
    9, 13,
    17, 25,
    33, 49,
    65, 97,
    129 , 193 ,
    257 , 385 ,
    513 , 769 ,
    1025 , 1537 ,
    2049 , 3073 ,
     4097 , 6145 ,
    8193 , 12289 ,
    16385 , 24577
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
    13, 13,
    ]
    extra_value = 0

    for i in range(len(distance_base)):

        if(distance_base[i] <= distance and 
            distance <= distance_base[i] + 2 ** distance_extra[i] - 1):
            distance_symbol = i

            extra_value = distance - distance_base[i]
            extra_count = distance_extra[i]
            extra_bits = f"{extra_value:0{extra_count}b}"
            
            break

    return distance_symbol, extra_bits

def covert_to_event(tokens):
    """
    Parmeters (tokens -> list of tubles)
    Return (event_streams -> list of tubles)
    
    This funcation will be included in main.
    It will take the tokens from stage1.
    The output of this funcation will be needed in stage3.

    The output here will be in that form 
    [("LiteralEvent",97), ("LiteralEvent", 98), ("LiteralEvent" ,99)
     ("MatchEvent", 269, "01", 4, "1") ,("EndEvent", 256)
    ]
    """
    event_streams = []

    for token in tokens:
        if(token[0] == "literal"):
            event_streams.append(("LiteralEvent", token[1]))
        else:
            length_symbol, length_extra = len_encoding(token[1])
            distance_symbol, distance_extra = distance_encoding(token[2])

            event_streams.append(("MatchEvent", length_symbol, length_extra, 
                                distance_symbol,distance_extra))

    event_streams.append(("EndEvent", 256))

    return event_streams        
