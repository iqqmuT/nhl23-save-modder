"""
Usage:
python3 parse.py INDEX DATA OUTPUT

The script will read LZ4 compressed data from DATA file and
writes it as uncompressed to OUTPUT file.
"""

import argparse
import lz4.frame
from lib import IndexHandler

# compressed data from DATA file is saved here for debugging purposes
DEBUG_COMPRESSED_FILE = "database.tmp.lz4"

def trim_data(data):
    """
    Trims given data so it takes a few bytes away from the
    beginning and end.
    """
    return data[0x10 + 1:len(data) - 4]

def decompress(data, output):
    """Decompresses given data using LZ4 and writes to given filename."""
    decompressed = lz4.frame.decompress(data)
    with open(output, "wb") as fp:
        fp.write(decompressed)
        print(f"Uncompressed to: {output}")

def run(index_file, data_file, output):
    idx_handler = IndexHandler(index_file)
    idx_handler.read()
    entry = idx_handler.get_entry(IndexHandler.ENTRY_CONTENT)
    chunks = entry['chunks']

    with open(data_file, "rb") as f:
        data = f.read()
        compressed = None
        for chunk in chunks:
            print(f"chunk start: 0x{chunk['start']:02x} end: 0x{chunk['end']:02x}")
            chunk_data = data[chunk['start']:chunk['end']]
            if compressed is None:
                compressed = chunk_data
            else:
                compressed += chunk_data

        compressed = trim_data(compressed)
        decompress(compressed, output)

        with open(DEBUG_COMPRESSED_FILE, "wb") as fc:
            fc.write(compressed)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extracts database.db from NHL23 save file.')
    parser.add_argument('index_file')
    parser.add_argument('data_file')
    parser.add_argument('db_file')
    args = parser.parse_args()
    run(args.index_file, args.data_file, args.db_file)
