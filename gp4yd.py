import argparse
import dataclasses
import json
import os
import sys
from typing import List, Callable, Optional, IO
from xml.sax.saxutils import escape

import requests


@dataclasses.dataclass(frozen=True)
class Arguments:
    token: str
    output_filename: str


@dataclasses.dataclass(frozen=True)
class FileInfo:
    path: str
    dir: str
    basename: str
    size: int


@dataclasses.dataclass(frozen=True)
class SplitResult:
    matched: List[FileInfo]
    unmatched: List[FileInfo]


def split_list(data: List[FileInfo], test_func: Callable[[FileInfo], bool]) -> SplitResult:
    matched = []
    unmatched = []
    for x in data:
        if test_func(x):
            matched.append(x)
        else:
            unmatched.append(x)
    return SplitResult(matched=matched, unmatched=unmatched)


def dict_to_file_info(item: dict) -> FileInfo:
    file_path = item['path']
    prefix = 'disk:'
    if file_path.startswith(prefix):
        file_path = file_path[len(prefix):]
    dir_name, basename = os.path.split(file_path)
    return FileInfo(
        path=file_path,
        dir=dir_name,
        basename=basename,
        size=item['size']
    )


def get_child_name(*, parent_dir: str, path: str) -> Optional[str]:
    if path.startswith(parent_dir):
        path = path[len(parent_dir):].lstrip('/')
        if not path:
            return None
        return path.split('/')[0]
    else:
        return None


def read_token(filename: str) -> str:
    if not os.path.isfile(filename):
        raise argparse.ArgumentTypeError(f'token file not found: {filename}')
    if os.path.getsize(filename) > 1024:
        raise argparse.ArgumentTypeError(f'token file too big: {filename}')
    with open(filename, encoding='utf-8') as inp:
        return inp.read().strip()


def read_config(args: List[str]) -> Arguments:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-t',
        '--token-file',
        required=True,
        help='file with Yandex Disk API token'
    )
    parser.add_argument('output_filename', help='output file (.gpscan)')
    result = parser.parse_args(args)

    token = read_token(result.token_file)
    output_filename = result.output_filename
    if os.path.exists(output_filename):
        raise argparse.ArgumentTypeError(f'output file already exists: {output_filename}')

    return Arguments(token=token, output_filename=output_filename)


def read_yandex_disk_files(token: str) -> List[FileInfo]:
    batch_size = 1000
    url = 'https://cloud-api.yandex.net/v1/disk/resources/files'
    headers = {'Authorization': f'OAuth {token}'}
    params = {
        'limit': batch_size,
        'offset': 0,
        'fields': 'size,path'
    }
    items: List[FileInfo] = []
    while True:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code != 200:
            sys.exit(f'expected 200 from API but got {response.status_code}')
        data = json.loads(response.content)
        local_items = [dict_to_file_info(x) for x in data['items']]
        items.extend(local_items)
        print('offset=%d, items=%d' % (params['offset'], len(local_items)))
        if len(local_items) < batch_size:
            break
        params['offset'] += batch_size
    return items


def report_dir(*, io: IO, dir_path: str, subdir_basename: str, items: List[FileInfo]) -> None:
    split_result = split_list(items, lambda x: x.dir == dir_path)
    file_records = split_result.matched
    remainder = split_result.unmatched

    print('<Folder name="%s">' % escape(subdir_basename), file=io)

    for rec in file_records:
        print('<File name="%s" size="%s"/>' % (escape(rec.basename), rec.size), file=io)

    subdirectories = {get_child_name(parent_dir=dir_path, path=x.dir) for x in remainder}
    subdirectories.discard(None)

    for dir2 in sorted(subdirectories):
        full_path = dir_path.rstrip('/') + '/' + dir2.lstrip('/')

        # filter files
        local_split_result = split_list(
            remainder,
            lambda x: x.dir == full_path or x.dir.startswith(full_path + '/')
        )
        dir2files = local_split_result.matched
        remainder = local_split_result.unmatched

        report_dir(io=io, dir_path=full_path, subdir_basename=dir2, items=dir2files)

    if remainder:
        print('INTERNAL ERROR:', dir_path, 'remainder:', len(remainder), 'records', file=sys.stderr)

    print('</Folder>', file=io)


def write_grand_perspective_file(file_records: List[FileInfo], output_filename: str) -> None:
    header = """<?xml version="1.0" encoding="UTF-8"?>
<GrandPerspectiveScanDump appVersion="2.5.3" formatVersion="6">
<ScanInfo volumePath="/" volumeSize="0" freeSpace="0" scanTime="2023-07-27T16:15:34Z" fileSizeMeasure="physical">
"""

    footer = """</ScanInfo>
</GrandPerspectiveScanDump>"""

    with open(output_filename, 'w', encoding='utf-8') as out:
        print(header, file=out)
        report_dir(io=out, dir_path='/', subdir_basename='/', items=file_records)
        print(footer, file=out)


def main(args: List[str]) -> None:
    config = read_config(args)

    file_records = read_yandex_disk_files(config.token)
    write_grand_perspective_file(file_records, config.output_filename)


if __name__ == '__main__':
    main(sys.argv[1:])
