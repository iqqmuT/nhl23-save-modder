import argparse
import lz4.frame
import os
from lib import write64, IndexHandler

"""
Usage:
python3 pack.py INDEX DATA MODIFIED_DATABASE_FILE

The script will rebuild INDEX and DATA files by injecting
MODIFIED_DATABASE_FILE there.
"""

BUILD_DIR = 'build'

def read_file(filename):
    data = None
    with open(filename, 'rb') as f:
        data = f.read()
    return data

def compress(data):
    """
    Compresses given data using LZ4 and writes to given filename.
    There should be only 1 LZ4 Frame.

    Usage:
    https://python-lz4.readthedocs.io/en/stable/lz4.frame.html#lz4.frame.compress

    Specs for LZ4:
    https://android.googlesource.com/platform/external/lz4/+/HEAD/doc/lz4_Frame_format.md
    """
    compressed = lz4.frame.compress(
        data,
        # NHL23 uses these settings.
        # Figured out by studying specs and looking at save files
        block_size=lz4.frame.BLOCKSIZE_MAX64KB,
        block_linked=False,
        compression_level=3,
        content_checksum=True,
        block_checksum=False,
        store_size=False,
    )
    return compressed

def no_compress(db_file):
    """Remove this after testing."""
    with open(db_file, "rb") as f:
        return bytearray(f.read())

def replace_db(data, idx_handler, db_file):
    # read from INDEX file the information about the main content
    entry = idx_handler.get_entry(IndexHandler.ENTRY_CONTENT)
    chunks = entry['chunks']

    # compress (modified) database file with LZ4
    db_data = read_file(db_file)
    compressed = compress(db_data)

    # copy 17 bytes from original data as prefix
    pos = chunks[0]['start']
    compressed = data[pos:pos + 17] + compressed

    # After compressed data there is 32-bit value of
    # data length of uncompressed data
    compressed += len(db_data).to_bytes(4, byteorder='little')

    new_length = len(compressed)

    pos = 0
    for idx, chunk in enumerate(chunks):

        end_pos = pos + (chunk['end'] - chunk['start'])
        if idx == len(chunks) - 1:
            # last chunk: write remaining data
            end_pos = new_length

        # replace chunk data
        data[chunk['start']:chunk['end']] = compressed[pos:end_pos]
        pos = end_pos

    # compressed data length most probably changed, update the value
    pos = chunks[0]['start']
    # new length does not include 16 first bytes which contain
    # this length value and a marker
    write64(data, pos, new_length - 0x10)

    # create output directory
    try:
        os.mkdir(BUILD_DIR)
    except FileExistsError:
        pass

    # update index
    idx_handler.set_content_length(new_length)
    idx_handler.write(f'{BUILD_DIR}/INDEX')

    with open(f'{BUILD_DIR}/DATA', 'wb') as f:
        f.write(data)

    print(f'Files written to {BUILD_DIR}/')

def run(index_file, data_file, db_file):
    idx_handler = IndexHandler(index_file)
    idx_handler.read()

    data = bytearray(read_file(data_file))
    replace_db(data, idx_handler, db_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Rewrites NHL23 save file with database.db.')
    parser.add_argument('index_file')
    parser.add_argument('data_file')
    parser.add_argument('db_file')
    args = parser.parse_args()
    run(args.index_file, args.data_file, args.db_file)
