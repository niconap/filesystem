'''
Name: Nico Nap
UvAnetID: 14259338
Bachelor informatica

mfstool.py:
    DESCRIPTION HERE
'''

import sys
import struct

BLOCK_SIZE = 1024


def parse_superblock(sbdata):
    '''
    This function takes all the data from the superblock and puts it in the
    dictionary.

    Parameters:
        sbdata (bytes): The data from the superblock.

    Returns:
        sbdict (dict): The dictionary with all the data from the superblock.
    '''

    sbdict = {}

    idx = 0
    (sbdict["ninodes"],) = struct.unpack("<H", sbdata[idx: idx + 2])
    idx += 2
    (sbdict["nzones"],) = struct.unpack("<H", sbdata[idx: idx + 2])
    idx += 2
    (sbdict["imap_blocks"],) = struct.unpack("<H", sbdata[idx: idx + 2])
    idx += 2
    (sbdict["zmap_blocks"],) = struct.unpack("<H", sbdata[idx: idx + 2])
    idx += 2
    (sbdict["first_data"],) = struct.unpack("<H", sbdata[idx: idx + 2])
    idx += 2
    (sbdict["log_zone_size"],) = struct.unpack("<H", sbdata[idx: idx + 2])
    idx += 2
    (sbdict["max_size"],) = struct.unpack("<L", sbdata[idx: idx + 4])
    idx += 4
    (sbdict["magic"],) = struct.unpack("<H", sbdata[idx: idx + 2])
    idx += 2
    (sbdict["state"],) = struct.unpack("<H", sbdata[idx: idx + 2])
    idx += 2

    return sbdict


def listdir(diskimg, sbdict):
    '''
    This function lists all the directories and files in the root directory.

    Parameters:
        diskimg (file): The file of the disk image.
        sbdict (dict): The dictionary with all the data from the superblock.
    '''
    # The first data block (root) can be found at first_data_zone.
    f.seek(BLOCK_SIZE * sbdict["first_data"], 0)
    root_data = f.read(BLOCK_SIZE)

    # Iterate over root_data and print each directory name.
    for i in range(2, len(root_data), 16):
        (name,) = struct.unpack("<14s", root_data[i: i + 14])
        stripped = name.rstrip(b"\0")
        if len(stripped) != 0:
            sys.stdout.buffer.write(stripped)
            sys.stdout.buffer.write(b'\n')


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: mfstool.py image command params")
        sys.exit(0)

    diskimg = sys.argv[1]
    cmd = sys.argv[2]

    with open(diskimg, "rb") as f:
        # Skip boot block
        f.seek(BLOCK_SIZE, 0)
        # Read super block
        sbdata = f.read(BLOCK_SIZE)

        sbdict = parse_superblock(sbdata)

        if cmd == 'ls':
            listdir(f, sbdict)
