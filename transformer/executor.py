"""
Execute plan, copying/renaming TV files from original to plexified repo
"""
import json
import os
import shutil


MAPPINGS_FILE = '/Users/emelz/Documents/code/tv-transformer/data/mappings.json'
MAPPINGS_TO_SKIP = 101


def read_mappings(mappings_file=MAPPINGS_FILE):
    f = open(mappings_file, 'r')
    lines = f.readlines()
    f.close()
    mappings = []
    for line in lines:
        mapping = json.loads(line)
        mappings.append(mapping)
    return mappings


def process_mapping(mapping):
    src = mapping['src']
    dest = mapping['dest']
    print(f'processing mapping {src} -> {dest}...', end='')
    if os.path.exists(dest):
        print("EXISTS, SKIPPING")
    else:
        dest_dir = os.path.dirname(dest)
        if not os.path.exists(dest_dir):
            print(f"creating {dest_dir}....", end='')
            os.mkdir(dest_dir)
        print(f"copying...", end='')
        shutil.copyfile(src, dest)
        print()


def process_mappings(mappings):
    count = 0
    for mapping in mappings:
        count += 1
        if MAPPINGS_TO_SKIP is not None and count <= MAPPINGS_TO_SKIP:
            continue
        process_mapping(mapping)


def execute():
    mappings = read_mappings()
    process_mappings(mappings)


if __name__ == '__main__':
    execute()
