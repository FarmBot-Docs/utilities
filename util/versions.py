#!/usr/bin/env python3

'Version utilities.'

import os
import json
from util.walk import is_content_dir


def color(text, text_color='red'):
    'color terminal text'
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'bold': '\033[1m',
        'end': '\033[0m',
    }
    return f'{colors[text_color]}{text}{colors["end"]}'


def get_version_from_root(root, index=2):
    'get doc version'
    version = root.split('/')[index]
    if version == 'docs':
        return 'docs'
    return float(version.strip('v'))


def get_content_versions(hub):
    'get version content directories'
    hub_dir = f'farmbot-{hub}'
    if not os.path.exists(hub_dir):
        return []
    sub_dirs = os.listdir(hub_dir)
    return [get_version_from_root(p, 0) for p in sub_dirs if is_content_dir(p)]


def genesis_stable_versions():
    'get genesis hub stable versions'
    return sorted([v for v in get_content_versions('genesis') if v > 1.1])


def latest_stable_versions(hub):
    'Get latest stable versions.'
    versions = get_content_versions(hub)
    max_version = [max(versions)] if len(versions) > 0 else []
    if max_version == [1.6]:
        return [1.5]
    return max_version


INTEGERS = {
    'software',
    'developers',
    'meta',
}


def get_version_string(hub, version_number):
    'Get version string from number.'
    if version_number == 'docs':
        return 'docs'
    if hub in INTEGERS:
        version_number = int(version_number)
    return f'v{version_number}'


def get_hub_from_dir(hub_dir):
    'Get hub name from directory.'
    return hub_dir.split('/')[-1].split('-')[-1]


HUBS = [
    'express',
    'genesis',
    'software',
    'developers',
    'meta',
    'oer',
]

HUBS_WITH_UNSTABLE_VERSIONS = [
    'genesis',
    'software',
    'developers',
]

HUB_STABLE_VERSIONS = {}
for hub_name in HUBS_WITH_UNSTABLE_VERSIONS:
    if hub_name == 'genesis':
        HUB_STABLE_VERSIONS[hub_name] = genesis_stable_versions()
    else:
        HUB_STABLE_VERSIONS[hub_name] = latest_stable_versions(hub_name)

print('All versions in unlisted hubs and versions below should be error-free:')
print(json.dumps(HUB_STABLE_VERSIONS, indent=2))


def stable_version_lookup():
    'get all stable versions for documentation'
    return HUB_STABLE_VERSIONS
