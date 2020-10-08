#!/usr/bin/env python3

'Directory walking utilities.'

import os


def get_local_root(folder, root):
    'remove current directory from path'
    local_start = len(folder.split('/')) + 1
    return os.sep.join(root.split('/')[local_start:])


def get_indent(local_root):
    'get indentation for current path depth'
    depth = len(local_root.split('/'))
    return ' ' * depth


def is_version_name(name):
    'check if the provided name is a version directory name'
    try:
        float(name.strip('v'))
    except ValueError:
        return False
    return True


def is_content_dir(local_root):
    'check if a directory should be entered'
    return is_version_name(local_root.split('/')[0])


def print_hub_title(hub):
    'print hub title'
    hub_title = f'farmbot-{hub}'
    print(f' {hub_title} '.center(100, '='))


def print_dir(local_root, verbose=False):
    'print a directory name with indentation'
    if not verbose:
        if is_version_name(local_root):
            print(local_root, end=' ', flush=True)
        return
    indent = get_indent(local_root)
    if is_version_name(local_root):
        print(f' {local_root} '.center(50, '_'))
    else:
        print(f'{indent}{local_root}')


def walk_through_files(folder, directory, parse_lines, verbose=False, quiet=False):
    'use parse_lines on the lines of each markdown file in a directory'
    for root, _dirs, files in sorted(os.walk(directory)):
        local_root = get_local_root(folder, root)
        if not is_content_dir(local_root):
            continue
        indent = get_indent(local_root)
        if not quiet:
            print_dir(local_root, verbose)
        files = [f for f in files if f.endswith('.md')]
        for filename in files:
            if not quiet and verbose:
                print(f'{indent * 2}{filename}')
            with open(os.path.join(root, filename), 'r') as md_file:
                lines = md_file.readlines()
                parse_lines(root, filename, lines)
    if not quiet:
        print()


def get_relative_filename(filename):
    'get a file path relative to script folder'
    script_folder = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(script_folder, '..', filename)
