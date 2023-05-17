'''
Name: Nico Nap
UvAnetID: 14259338
Bachelor informatica

mfstool.py:
    DESCRIPTION HERE
'''

import sys
import struct
import math

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


def parse_inode_table(f, sbdict):
    inode_table_offset = BLOCK_SIZE * 2 + \
        (math.ceil(sbdict['ninodes'] / 8 / BLOCK_SIZE) * BLOCK_SIZE) + \
        (math.ceil(sbdict['nzones'] / 8 / BLOCK_SIZE) * BLOCK_SIZE)
    f.seek(inode_table_offset, 0)
    inode_table_data = f.read(BLOCK_SIZE)
    inode_dict = {}

    idx = 0
    (inode_dict['mode'],) = struct.unpack("<H", inode_table_data[idx: idx + 2])
    idx += 2
    (inode_dict['uid'],) = struct.unpack("<H", inode_table_data[idx: idx + 2])
    idx += 2
    (inode_dict['size'],) = struct.unpack("<L", inode_table_data[idx: idx + 4])
    idx += 4
    (inode_dict['mtime'],) = struct.unpack(
        "<L", inode_table_data[idx: idx + 4])
    idx += 4
    (inode_dict['gid'],) = struct.unpack("<B", inode_table_data[idx: idx + 1])
    idx += 1
    (inode_dict['nlinks'],) = struct.unpack(
        "<B", inode_table_data[idx: idx + 1])
    idx += 1
    (inode_dict['zone0'],) = struct.unpack(
        "<H", inode_table_data[idx: idx + 2])
    idx += 2
    (inode_dict['zone1'],) = struct.unpack(
        "<H", inode_table_data[idx: idx + 2])
    idx += 2
    (inode_dict['zone2'],) = struct.unpack(
        "<H", inode_table_data[idx: idx + 2])
    idx += 2
    (inode_dict['zone3'],) = struct.unpack(
        "<H", inode_table_data[idx: idx + 2])
    idx += 2
    (inode_dict['zone4'],) = struct.unpack(
        "<H", inode_table_data[idx: idx + 2])
    idx += 2
    (inode_dict['zone5'],) = struct.unpack(
        "<H", inode_table_data[idx: idx + 2])
    idx += 2
    (inode_dict['zone6'],) = struct.unpack(
        "<H", inode_table_data[idx: idx + 2])
    idx += 2
    (inode_dict['indirect'],) = struct.unpack(
        "<H", inode_table_data[idx: idx + 2])
    idx += 2
    (inode_dict['double'],) = struct.unpack(
        "<H", inode_table_data[idx: idx + 2])
    idx += 2

    print("inode: " + str(inode_dict))


def listdir(f, sbdict, block_nr):
    '''
    This function lists all the directories and files in the root directory.

    Parameters:
        diskimg (file): The file of the disk image.
        sbdict (dict): The dictionary with all the data from the superblock.
    '''

    # The first data block (root) can be found at first_data_zone.
    f.seek(BLOCK_SIZE * (sbdict["first_data"] + block_nr), 0)
    root_data = f.read(BLOCK_SIZE)

    if sbdict["magic"] == 0x137F:
        name_len = 14
    else:
        name_len = 30

    # Iterate over root_data and print each directory name.
    for i in range(2, len(root_data), name_len + 2):
        (name,) = struct.unpack(
            "<" + str(name_len) + "s", root_data[i: i + name_len])
        printname = name.rstrip(b"\0")
        if len(printname) != 0:
            sys.stdout.buffer.write(printname)
            sys.stdout.buffer.write(b"\n")

    # TO-DO: Go to the next block using the inodes.


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

        print("superblock: " + str(sbdict))

        parse_inode_table(f, sbdict)

        if cmd == 'ls':
            listdir(f, sbdict, 0)
