import argparse

from stage1.LZ77 import lz77_compress
from stage2.deflate_symboles import covert_to_event
from stage3.huffman import *
from stage4.stage4 import compress_stage4, decompress_stage4


parser = argparse.ArgumentParser(
    description="A DEFLATE-based file compressor and decompressor"
    )
parser.add_argument('filename',type=str,
                    help="Name of file you want to compress!")
parser.add_argument('-c', '--compress', action='store_true',
                    help="Compress the given file")
parser.add_argument('-d', '--decompress', action='store_true',
                    help="Decompress the given file")

args = parser.parse_args()

if args.compress:
    with open(args.filename, "r") as f:
        data = f.read()

    data_byte = data.encode("utf-8")

    tokens = lz77_compress(data_byte)
    event_streams = covert_to_event(tokens)

    lit_freq, dist_freq = count_frequencies(event_streams)
    lit_lengths = build_huffman_lengths(lit_freq, 286)
    dist_lengths = build_huffman_lengths(dist_freq, 30)
    lit_codes = canonical_huffman(lit_lengths)
    dist_codes = canonical_huffman(dist_lengths)

    with open("data.txt.sdfl", "xb") as f:
        f.write(compress_stage4(event_streams, lit_codes, dist_codes))

    print(f"Compressed: {args.filename} -> data.txt.sdfl")

elif args.decompress:
    with open(args.filename, "rb") as f:
        uncompressed = decompress_stage4(f.read())

    with open("data.txt", "xb") as f:
        f.write(uncompressed)
        
    print(f"DeCompressed: {args.filename} → data.txt")

else:
    print("Please specify -c to compress or -d to decompress")