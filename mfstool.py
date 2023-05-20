'''
Name: Nico Nap
UvAnetID: 14259338
Bachelor informatica

mfstool.py:
    This file contains functions that can be used to read the data from a
    minix file system disk image.
'''

import sys
import struct
import math
import time

BLOCK_SIZE = 1024
INODE_SIZE = 32


def parse_superblock(sbdata):
    '''
    This function takes all the data from the superblock and puts it in the
    dictionary.

    Input:
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


def parse_inode(f, sbdict, num):
    '''
    This function finds an inode and returns all of its data in a dictionary.

    Input:
        f (file): The file of the disk image.
        sbdict (dict): The dictionary with all the data from the superblock.
        num (int): The number of the inode.

    Returns:
        inode_dict (dict): The dictionary with all the data from the inode.
    '''
    inode_table_offset = BLOCK_SIZE * 2 + \
        (math.ceil(sbdict['ninodes'] / 8 / BLOCK_SIZE) * BLOCK_SIZE) + \
        (math.ceil(sbdict['nzones'] / 8 / BLOCK_SIZE) * BLOCK_SIZE) + \
        num * INODE_SIZE
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

    # The mode value is an octal number, so it has to be converted.
    inode_dict['mode'] = oct(inode_dict['mode'])

    return inode_dict


def parse_inode_map(f, sbdict):
    '''
    This function finds the inode map and returns all of its data in a
    dictionary.

    Input:
        f (file): The file of the disk image.
        sbdict (dict): The dictionary with all the data from the superblock.

    Returns:
        inode_map (list): The list with the bytes from the inode map.
    '''
    f.seek(BLOCK_SIZE * 2, 0)
    inode_map_data = f.read(
        math.ceil(sbdict['ninodes'] / 8 / BLOCK_SIZE) * BLOCK_SIZE)
    inode_bits = ''.join(f'{byte:08b}' for byte in inode_map_data)

    inode_map = []
    for i in range(0, len(inode_bits), 8):
        inode_map.append(inode_bits[i:i + 8])

    return inode_map


def find_inode(f, sbdict, path):
    '''
    This function finds the inode number of the file or directory specified by
    path. This function returns -1 when the file or directory was not found.

    Input:
        f (file): The file of the disk image.
        path (str): The path of the file.
        sbdict (dict): The dictionary with all the data from the superblock.

    Returns:
        inode_num (int): The inode number of the file (index starts at 0).
    '''
    # Parse the path name and encode it.
    path = path.split('/')
    root_inode = parse_inode(f, sbdict, 0)

    if sbdict["magic"] == 0x137F:
        name_len = 14
    else:
        name_len = 30

    i = 0
    while True:
        if root_inode[f"zone{i}"] == 0:
            break
        f.seek(BLOCK_SIZE * root_inode[f"zone{i}"], 0)
        root_data = f.read(BLOCK_SIZE)
        dirswitch = False

        # Iterate over each dir entry to find the next dir or file.
        for j in range(2, len(root_data), name_len + 2):
            name = struct.unpack(
                f"<{name_len}s", root_data[j: j + name_len])[0]
            inode_num = struct.unpack("<H", root_data[j - 2: j])[0]

            name_str = name.rstrip(b"\0").decode()

            if len(path) > 1 and name_str == path[0]:
                root_inode = parse_inode(f, sbdict, inode_num - 1)
                path.pop(0)
                dirswitch = True
                break
            elif name_str == path[0]:
                return inode_num - 1

        if dirswitch:
            i = 0
        else:
            i += 1

    return -1


def create_inode(f, sbdict, type):
    '''
    This function creates a new inode and returns the inode number.

    Input:
        f (file): The file of the disk image.
        sbdict (dict): The dictionary with all the data from the superblock.
        type (str): The type of the inode (f for file or d for directory).

    Side effects:
        The inode map is updated and the inode table is updated.

    Returns:
        inode_num (int): The inode number of the new inode (index starts at 0).
    '''
    if type != 'f' and type != 'd':
        sys.stderr.buffer.write(("Error: invalid type").encode())
        return -1
    inode = {}
    inode['mode'] = 0o100664 if type == 'f' else 0o40775
    inode['mode'] = oct(inode['mode'])
    inode['uid'] = 0
    inode['size'] = 0
    inode['mtime'] = time.time()
    inode['gid'] = 0
    inode['nlinks'] = 1
    inode['zone0'] = 0
    inode['zone1'] = 0
    inode['zone2'] = 0
    inode['zone3'] = 0
    inode['zone4'] = 0
    inode['zone5'] = 0
    inode['zone6'] = 0
    inode['indirect'] = 0
    inode['double'] = 0

    # Find the first free inode using the inode map.
    inode_map = parse_inode_map(f, sbdict)
    idx = 0
    while inode_map[idx] == '11111111':
        idx += 1
    current_bit = inode_map[idx][::-1].index('0')
    inode_num = idx * 8 + current_bit - 1

    # Update the inode map and add the inode to the inode table.
    inode_map[idx] = inode_map[idx][:7 - current_bit] + '1' + \
        inode_map[idx][7 - current_bit + 1:]
    f.seek(BLOCK_SIZE * 2 + idx * 8, 0)
    f.write(bytes([int(inode_map[idx], 2)]))
    f.seek(BLOCK_SIZE * 2 + sbdict['ninodes'] * 32 + inode_num * 32, 0)
    for key in inode:
        if key == 'mode':
            f.write(struct.pack("<H", int(inode[key], 8)))
        else:
            f.write(struct.pack("<I", int(inode[key])))

    return inode_num


def listdir(f, sbdict, path):
    '''
    This function lists all the directories and files in the directory
    specified by path.

    Input:
        diskimg (file): The file of the disk image.
        sbdict (dict): The dictionary with all the data from the superblock.
        path (str): The path of the directory.

    Side effects:
        The contents of the directory are printed to the console.
    '''
    if path == '/':
        inode_num = 0
    else:
        inode_num = find_inode(f, sbdict, path)
    if inode_num == -1:
        sys.stderr.buffer.write(
            (f"Error: directory {path} not found").encode())
        return

    inode = parse_inode(f, sbdict, inode_num)
    if int(inode['mode'], 8) < 0o40000 or int(inode['mode'], 8) > 0o40777:
        sys.stderr.buffer.write((f"Error: {path} is not a directory").encode())
        return

    for i in range(7):
        f.seek(BLOCK_SIZE * inode[f"zone{i}"], 0)
        root_data = f.read(BLOCK_SIZE)

        if sbdict["magic"] == 0x137F:
            name_len = 14
        else:
            name_len = 30

        for i in range(2, len(root_data), name_len + 2):
            (name,) = struct.unpack(
                "<" + str(name_len) + "s", root_data[i: i + name_len])
            printname = name.rstrip(b"\0")
            if len(printname) != 0:
                sys.stdout.buffer.write(printname)
                sys.stdout.buffer.write(b"\n")


def catfile(f, sbdict, path):
    '''
    This function prints the contents of the file specified by path.

    Input:
        f (file): The file of the disk image.
        sbdict (dict): The dictionary with all the data from the superblock.
        path (str): The path of the file.
    '''
    inode_num = find_inode(f, sbdict, path)
    if inode_num == -1:
        sys.stderr.buffer.write(
            (f"Error: the file {path} does not exist").encode())
        sys.exit(0)

    inode = parse_inode(f, sbdict, inode_num)
    if 0o100444 <= int(inode['mode'], 8) <= 0o120000:
        for i in range(7):
            if inode[f"zone{i}"] == 0:
                break
            f.seek(BLOCK_SIZE * inode[f"zone{i}"], 0)
            sys.stdout.buffer.write(f.read(BLOCK_SIZE).rstrip(b"\0"))
    else:
        sys.stderr.buffer.write(
            (f"Error: {path} is not a file or is not readable").encode())
        sys.exit(0)


def touchfile(f, sbdict, path):
    '''
    This function creates a new file at the specified path. If the file already
    exists, nothing happens.

    Input:
        f (file): The file of the disk image.
        sbdict (dict): The dictionary with all the data from the superblock.
        path (str): The path of the file.

    Side effects:
        Creates a new file at the specified path in the disk image.
    '''
    if find_inode(f, sbdict, path) != -1:
        return

    inode_num = create_inode(f, sbdict, 'f')
    # TO DO: add a directory entry to the directory in the path. If the
    # directory does not exist -> error. Later we will implement mkdir, which can
    # then be used to create a new dir.


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: mfstool.py image command params")
        sys.exit(0)

    diskimg = sys.argv[1]
    cmd = sys.argv[2]
    if len(sys.argv) > 3:
        path = sys.argv[3]

    with open(diskimg, "rb") as f:
        f.seek(BLOCK_SIZE, 0)
        sbdata = f.read(BLOCK_SIZE)

        sbdict = parse_superblock(sbdata)
        print(sbdict)
        if cmd == 'ls':
            if len(sys.argv) > 3:
                listdir(f, sbdict, path)
            else:
                listdir(f, sbdict, "/")
        elif cmd == 'cat':
            if (len(sys.argv) < 4):
                print("Usage: mfstool.py image cat file")
                sys.exit(0)
            catfile(f, sbdict, path)
        elif cmd == 'touch':
            if (len(sys.argv) < 4):
                print("Usage: mfstool.py image touch file")
                sys.exit(0)
            touchfile(f, sbdict, path)
