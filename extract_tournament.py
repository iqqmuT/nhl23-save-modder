"""
Usage:
python3 parse.py TOURNAMENT_FILE

The script will read multiple LZ4 compressed data from DATA file and
writes it as uncompressed to OUTPUT file.
"""

import argparse
import lz4.frame
import os

from lib import TournamentHandler, read_lz4_frame_length

# we can detect frames by this
# actual LZ4 frame magic number does not include 0x01
# but here we seem to have it
LZ4_MAGIC_NUMBER = b'\x01\x04\x22\x4D\x18'

def new_filename(filename, nbr):
    base, ext = os.path.splitext(filename)
    return f'{base}_{nbr}{ext}'

def decompress(data, output):
    """Decompresses given data using LZ4 and writes to given filename."""
    decompressed = lz4.frame.decompress(data)
    with open(output, "wb") as fp:
        fp.write(decompressed)
        print(f"Decompressed to: {output}")

def write_debug_file(data, i):
    output = new_filename('debug_tournament.txt', i)
    with open(output, 'wb') as fp:
        # all frames begin with 0x01
        fp.write(b'\x01')
        fp.write(data)

def find_frames(data):
    """Finds all LZ4 frames from the data and returns list of positions."""
    positions = []
    i = 0
    while True:
        pos = data.find(LZ4_MAGIC_NUMBER, i)
        if pos == -1:
            break

        end = read_lz4_frame_length(data, pos + 1)
        positions.append((pos + 1, end)) # skip preceding 0x01
        i = pos + 1
    return positions

def write_file(filename, data):
    #filename = 'tournament_footer.dat'
    with open(filename, 'wb') as ff:
        ff.write(data)
    print(f'Data copied to: {filename}')

def run(data_file, output):
    handler = TournamentHandler()
    data, entries = handler.read(data_file)

    i = 0
    start = 0
    end = 0
    for entry in entries:
        start, end = entry
        entry_output = new_filename(output, i)
        if i < 5:
            # each compressed entry starts with 0x01 marker, skip it
            compressed = data[start + 1:end]
            # decompress
            decompress(compressed, entry_output)
        else:
            # copy data as-is
            write_file(entry_output, data[start:end])
        i += 1

    # write remaining data
    entry_output = new_filename(output, i)
    write_file(entry_output, data[end:])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extracts files from NHL23 tournament file.')
    parser.add_argument('tournament_file')
    parser.add_argument('output_file')
    args = parser.parse_args()
    run(args.tournament_file, args.output_file)
