import argparse
import lz4.frame
from lib import TournamentHandler

"""
Usage:
python3 pack.py INDEX DATA MODIFIED_DATABASE_FILE

The script will rebuild INDEX and DATA files by injecting
MODIFIED_DATABASE_FILE there.
"""

#BUILD_DIR = 'build'

def compress(input_file):
    """
    Compresses given data using LZ4 and writes to given filename.
    There should be only 1 LZ4 Frame.

    Usage:
    https://python-lz4.readthedocs.io/en/stable/lz4.frame.html#lz4.frame.compress

    Specs for LZ4:
    https://android.googlesource.com/platform/external/lz4/+/HEAD/doc/lz4_Frame_format.md
    """
    with open(input_file, "rb") as f:
        data = f.read()
    compressed = lz4.frame.compress(
        data,
        # NHL23 uses these settings.
        # Figured out by studying specs and looking at save files
        block_size=lz4.frame.BLOCKSIZE_MAX64KB,
        block_linked=False,
        compression_level=9,
        content_checksum=True,
        block_checksum=False,
        store_size=False,
    )
    return compressed

def no_compress(db_file):
    """Remove this after testing."""
    with open(db_file, "rb") as f:
        return bytearray(f.read())

def read_file(input_file):
    data = None
    with open(input_file, 'rb') as f:
        data = bytearray(f.read())
    return data

def run(output_file, input_files):
    entries = []
    start = 0
    end = 0
    with open(output_file, 'wb') as output:
        #data = bytearray(f.read())
        #replace_db(data, idx_handler, db_file)
        #output.write(b'\x01')
        i = 0
        for input_file in input_files:
            start = output.tell()

            if i < 5:
                print(f'Compressing {input_file}')
                compressed = compress(input_file)
                #data = read_file(input_file)
                # each compressed frame begins with 0x01 in tournament file
                output.write(b'\x01')
                output.write(compressed)
            elif i < len(input_files) - 1:
                print(f'Copying {input_file}')
                # this data is already compressed, copy as-is
                data = read_file(input_file)
                output.write(data)
            else:
                # last part which is index
                print(f'Updating and writing index {input_file}')
                print(f'Entries: {entries}')
                data = read_file(input_file)
                handler = TournamentHandler()
                handler.update_entries(data, entries)
                output.write(data)

            end = output.tell()
            entries.append((start, end))
            i += 1

            #if i < len(input_files):
                # ignore last part because it is index, not an entry
            #output.write(data) # debug

    # append special uncompressed footer data

    #footer_file = 'tournament_footer.dat'
    #print(f'Appending {footer_file}')
    #footer = read_file(footer_file)
    #output.write(footer)

    print(f'{output_file} written.')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Rewrites NHL23 save file with database.db.')
    parser.add_argument('output_file')
    parser.add_argument('input_files', nargs='+', help='Uncompressed tournament files')
    args = parser.parse_args()
    run(args.output_file, args.input_files)
