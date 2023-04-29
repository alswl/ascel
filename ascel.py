#!/usr/bin/env python3
# coding= utf-8

import struct
import os
import sys


def read_utf16_str(scel_file, offset=-1, len=2):
    if offset >= 0:
        scel_file.seek(offset)
    str = scel_file.read(len)
    return str.decode('UTF-16LE')


def read_uint16(scel_file):
    return struct.unpack('<H', scel_file.read(2))[0]


def get_word_from_sogou_cell_dict(scel_file, scel_file_size):
    hz_offset = 0
    mask = struct.unpack('B', scel_file.read(128)[4:5])[0]

    if mask == 0x44:
        hz_offset = 0x2628
    elif mask == 0x45:
        hz_offset = 0x26c4
    else:
        sys.exit(1)

    ## get scel information
    scel_title = read_utf16_str(scel_file, 0x130, 0x338 - 0x130)
    scel_type = read_utf16_str(scel_file, 0x338, 0x540 - 0x338)
    scel_desc = read_utf16_str(scel_file, 0x540, 0xd40 - 0x540)
    scel_samples = read_utf16_str(scel_file, 0xd40, 0x1540 - 0xd40)

    py_map = {}

    ## prepare all pinyin map
    scel_file.seek(0x1540 + 4)

    while True:
        py_code = read_uint16(scel_file)
        py_len = read_uint16(scel_file)
        py_str = read_utf16_str(scel_file, -1, py_len)

        if py_code not in py_map:
            py_map[py_code] = py_str

        if py_str == 'zuo':  # end of pinyin list
            break
    scel_file.seek(hz_offset)

    ## loop and generate pinyin + word
    try:
        while True:
            word_count = read_uint16(scel_file)
            pinyin_count = read_uint16(scel_file) / 2

            pinyin_list = []
            for i in range(pinyin_count):
                py_id = read_uint16(scel_file)
                try:
                    pinyin_list.append(py_map[py_id])
                except KeyError:
                    pinyin_list = []

            for i in range(word_count):
                word_len = read_uint16(scel_file)
                word_string = read_utf16_str(scel_file, -1, word_len)
                scel_file.read(12)
                yield pinyin_list, word_string
    except Exception:
        yield [], ''
    scel_file.close()


def show_txt(records):
    for (pinyin_list, word) in records:
        print(' '.join(pinyin_list), word)


def show_rime(records):
    for (pinyin_list, word) in records:
        print('%s\t%s' % (word, ' '.join(pinyin_list)))


def main():
    assert len(sys.argv) == 2
    scel_file_path = sys.argv[1]

    with open(scel_file_path, "rb") as scel_file:
        scel_file_size = os.path.getsize(scel_file_path)
        generator = get_word_from_sogou_cell_dict(scel_file, scel_file_size)
        # show_txt(generator)
        show_rime(generator)


if __name__ == "__main__":
    main()
