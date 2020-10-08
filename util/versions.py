#!/usr/bin/env python3

'Version utilities.'

import json
from util.walk import get_relative_filename


def stable_version_lookup():
    'get all stable versions for documentation'
    filename = get_relative_filename('STABLE_VERSIONS.json')
    with open(filename, 'r') as stable_versions_file:
        return json.load(stable_versions_file)
