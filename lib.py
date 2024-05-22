"""
Common library.
"""

def read32(data, pos):
    """Returns 32 bit integer from data."""
    int32_bytes = data[pos:pos + 4]
    int32_val = int.from_bytes(
        int32_bytes,
        byteorder='little',
        signed=False,
    )
    return int32_val

def read64(data, pos):
    """Returns 64 bit integer from data."""
    int64_bytes = data[pos:pos + 8]
    int64_val = int.from_bytes(
        int64_bytes,
        byteorder='little',
        signed=False,
    )
    return int64_val

def write32(data, pos, int_value):
    """Overwrites 32 bit integer into data with given pos."""
    data[pos:pos + 4] = int_value.to_bytes(4, byteorder='little')

def write64(data, pos, int_value):
    """Overwrites 64 bit integer into data with given pos."""
    data[pos:pos + 8] = int_value.to_bytes(8, byteorder='little')

def read_until_zero(data):
    """Reads bytearray from data until 0x00 is found."""
    result = bytearray()
    for byte in data:
        if byte == 0:
            break
        result.append(byte)
    return result

def read_lz4_frame_length(data, pos):
    """
    Returns position where LZ4 compressed frame ends.
    Given pos must be position of LZ4 magic number (0x184D2204).
    """
    if read32(data, pos) != 0x184D2204:
        raise Exception(f'read_lz4_frame_length ERROR: no LZ4 compressed data found at pos {pos}')
    i = pos + 7
    while i < len(data):
        # each data block begins with block size
        block_size = read32(data, i)
        if block_size == 0:
            # we found end mark, return length of read data
            # after end mark we have 32 bit checksum
            return i + 8
        i += 4 + block_size
    return None

class IndexHandler():
    """
    Handler for NHL23 CustomRoster INDEX save file.
    INDEX file tells data chunk (entry) positions and lengths.
    """
    ENTRY_CONTENT = 'content' # entry where compressed database is
    ENTRY_SAVE_LOAD_FILE_INFO = b'__SaveLoadFileInfo'
    ENTRY_SAVE_LOAD_META_DATA = b'__SaveLoadMetaData'
    ENTRY_SAVE_LOAD_VER = b'__SaveloadVer'

    def __init__(self, filename):
        self.filename = filename
        self.entries = {}

    def _find_entry(self, name):
        """Returns start position of given entry."""
        pos = 0
        while pos < len(self.data):
            pos_name = read_until_zero(self.data[pos:])
            if pos_name == name:
                return pos
            if name == self.ENTRY_CONTENT and pos_name not in [self.ENTRY_SAVE_LOAD_FILE_INFO, self.ENTRY_SAVE_LOAD_META_DATA, self.ENTRY_SAVE_LOAD_VER]:
                return pos
            # next entry pos depends on chunk count
            pos += self.data[pos + 0x20] * 0x20 + 0x30
        raise Exception(f'ERROR: Could not find entry "{name}" from INDEX file')

    def _validate_chunks(self, entry):
        """Validates entry, makes sure data is valid."""
        sum_length = 0
        for chunk in entry['chunks']:
            sum_length += chunk['end'] - chunk['start']
        if sum_length != entry['total_length']:
            raise Exception(f'VALIDATION ERROR: chunk lengths of entry "{entry["name"]}" do not match: {sum_length} != {entry["total_length"]}')

    def _read_entry(self, name):
        entry = {
            'name': name,
            'chunks': [],
        }
        pos = self._find_entry(name)

        # move to position where it says the count of chunks
        # and total length of entry data
        pos += 0x20
        chunk_count = read64(self.data, pos)
        entry['total_length'] = read64(self.data, pos + 8)

        i = 0
        while i < chunk_count:
            pos += 0x10
            start_pos = read64(self.data, pos)

            pos += 8
            end_pos = read64(self.data, pos)

            entry['chunks'].append({
                'start': start_pos,
                'end': end_pos,
            })
            pos += 8
            i += 1

        self._validate_chunks(entry)
        self.entries[name] = entry

    def _link_chunks(self):
        """
        All entry chunks should be next to each other.
        Find the order of chunks and add self.first_entry
        and 'next' property for each entry.
        """
        def find_chunk_by_start(start):
            for entry in self.entries.values():
                for idx, chunk in enumerate(entry['chunks']):
                    if chunk['start'] == start:
                        return (entry['name'], idx)
            return None

        # find first entry
        self.ordered_chunks = []
        result = find_chunk_by_start(0)
        self.ordered_chunks.append(result)

        while result is not None:
            name, chunk = result
            end_pos = self.entries[name]['chunks'][chunk]['end']
            result = find_chunk_by_start(end_pos)
            if result is not None:
                self.ordered_chunks.append(result)

    def read(self):
        with open(self.filename, "rb") as f:
            self.data = bytearray(f.read())

            self._read_entry(self.ENTRY_CONTENT)
            self._read_entry(self.ENTRY_SAVE_LOAD_FILE_INFO)
            self._read_entry(self.ENTRY_SAVE_LOAD_META_DATA)
            self._read_entry(self.ENTRY_SAVE_LOAD_VER)
            self._link_chunks()

    def get_entry(self, name):
        return self.entries[name]

    def set_positions(self, entry_name, chunk_idx, start_pos, end_pos):
        self.entries[entry_name]['chunks'][chunk_idx]['start'] = start_pos
        self.entries[entry_name]['chunks'][chunk_idx]['end'] = end_pos

        # find the position
        pos = self._find_entry(entry_name)
        pos += 0x30
        i = 0
        while i < chunk_idx:
            pos += 0x20
            i += 1

        # modify self.data
        write64(self.data, pos, start_pos)
        write64(self.data, pos + 8, end_pos)

    def find_ordered_chunk(self, name, idx):
        """Returns index of matching entry chunk from self.ordered_chunks."""
        for i, item in enumerate(self.ordered_chunks):
            if item[0] == name and item[1] == idx:
                return i
        raise Exception(f"IndexHandler::find_ordered_chunk no results: {name} {idx}")

    def set_content_length(self, new_length):
        # modify self.data with the new content length
        pos = self._find_entry(self.ENTRY_CONTENT)
        pos += 0x28
        write64(self.data, pos, new_length)

        entry = self.entries[self.ENTRY_CONTENT]
        old_length = entry['total_length']
        diff = new_length - old_length

        # find the last content chunk from self.ordered_chunks
        i = self.find_ordered_chunk(
            self.ENTRY_CONTENT,
            len(entry['chunks']) - 1,
        )

        first = True
        while i < len(self.ordered_chunks):
            entry_name, chunk_idx = self.ordered_chunks[i]
            entry = self.entries[entry_name]
            new_start = entry['chunks'][chunk_idx]['start']
            if not first:
                # do not change start position for the first chunk,
                # but change it for all the following chunks
                new_start += diff
            new_end = entry['chunks'][chunk_idx]['end'] + diff
            self.set_positions(
                entry_name,
                chunk_idx,
                new_start,
                new_end,
            )
            first = False
            i += 1

    def write(self, output):
        with open(output, "wb") as f:
            f.write(self.data)
