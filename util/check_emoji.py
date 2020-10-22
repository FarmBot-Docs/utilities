#!/usr/bin/env python3

'Verify emoji in documentation markdown files.'

import os
import json
import string
from urllib.request import Request, urlopen
from util import versions
from util import walk


def load_valid_emoji_names():
    'get list of valid emoji names'
    emojis_filename = walk.get_relative_filename('valid_emoji_names.json')
    if os.path.exists(emojis_filename):
        with open(emojis_filename, 'r') as emoji_f:
            valid_emoji_names = json.load(emoji_f)
    else:
        url = 'https://raw.githubusercontent.com/github/gemoji/master/db/emoji.json'
        request = Request(url)
        request.add_header('Accept', 'application/json')
        with urlopen(request) as response, open(emojis_filename, 'w') as emoji_f:
            data = json.loads(response.read())
            valid_emoji_names = []
            for emoji_data in data:
                for alias in emoji_data['aliases']:
                    valid_emoji_names.append(alias)
            json.dump(sorted(valid_emoji_names), emoji_f, indent=2)
    return valid_emoji_names


def is_not_available(**kwargs):
    'check if emoji is available'
    return kwargs['emoji'] not in kwargs['valid_emoji_names']


def uses_hyphens(**kwargs):
    'check if emoji uses hyphens'
    has_hyphen = '-' in kwargs['emoji']
    valid_hyphen_emojis = ['-1', 't-rex', 'e-mail', 'non-potable_water']
    return has_hyphen and kwargs['emoji'] not in valid_hyphen_emojis


POSSIBLE_ISSUES = {
    'not_available': {
        'label': 'not available',
        'check': is_not_available,
    },
    'uses_hyphens': {
        'label': 'uses hyphens instead of underscores',
        'check': uses_hyphens,
    },
}


def check_line(**kwargs):
    'verify links in line'
    line = kwargs['line']
    colon_count = len(line.split(':')) - 1
    if colon_count > 1:
        visited = []
        while len(visited) < colon_count:
            start_index = visited[-1] if len(visited) > 0 else 0
            start = line.index(':', start_index) + 1
            visited.append(start)
            next_colon = line.find(':', start)
            if next_colon is None:
                break
            visited.append(next_colon + 1)
            to_next = line[start:next_colon].lower()
            if len(to_next) < 1:
                continue
            valid = True
            for k in to_next:
                if k not in string.ascii_lowercase + string.digits + '+-_':
                    valid = False
                    break
            if not valid:
                continue
            end = next_colon
            emoji = line[start:end]
            if emoji.isdigit() and emoji not in ['100', '1234']:
                continue
            if emoji == 'backups':
                continue
            kwargs['check_emoji'](
                kwargs['root'],
                kwargs['filename'],
                emoji,
                kwargs['line_number'])


class EmojiChecker():
    'Check emoji in documentation. (default directory: current)'

    def __init__(self, summary, folder=None):
        self.summary = summary
        self.verbose = False
        self.folder = folder or '.'
        self.current_hub = None
        self.current_hub_path = None
        self.emojis = {}
        self.emoji_names = {
            'available': load_valid_emoji_names(),
            'used': set(),
            'bad': set(),
        }

    def check_emoji(self, root, filename, emoji, line_number):
        'verify integrity of emoji'
        local_root = walk.get_local_root(self.folder, root)
        emoji_check_kwargs = {
            'root': root,
            'filename': filename,
            'emoji': emoji,
            'current_hub': self.current_hub,
            'valid_emoji_names': self.emoji_names['available'],
        }
        issues = []
        for issue, issue_data in POSSIBLE_ISSUES.items():
            if issue_data['check'](**emoji_check_kwargs):
                issues.append(issue)
        status = 'ok'
        if len(issues) > 0:
            status = POSSIBLE_ISSUES[issues[0]]['label']
            self.emoji_names['bad'].add(emoji)
        emoji_info = {
            'status': status,
            'version': float(local_root.split('/')[0].strip('v')),
            'from': os.sep.join([local_root, filename]),
            'line_number': line_number,
            'emoji': emoji,
            'issues': issues,
        }
        self.emojis[self.current_hub].append(emoji_info)
        self.emoji_names['used'].add(emoji)
        if self.verbose:
            icon = 'X' if len(issues) > 0 else '|'
            print(f'{icon}{walk.get_indent(local_root) * 3}{emoji}')

    def check_emojis(self):
        'verify integrity of emojis in a directory'
        def _parse_lines(root, filename, lines):
            for line_number, line in enumerate(lines):
                line_check_kwargs = {
                    'check_emoji': self.check_emoji,
                    'filename': filename,
                    'root': root,
                    'line': line,
                    'line_number': line_number,
                }
                check_line(**line_check_kwargs)
        path = self.current_hub_path
        walk.walk_through_files(self.folder, path, _parse_lines, self.verbose)

    def check_all(self, hubs=None):
        'check emoji in all hubs'
        if hubs is None:
            hubs = versions.stable_version_lookup().keys()
        for hub in hubs:
            self.current_hub = hub
            self.emojis[hub] = []
            hub_title = f'farmbot-{hub}'
            self.current_hub_path = f'{self.folder}/{hub_title}'
            if os.path.exists(self.current_hub_path):
                if self.verbose:
                    walk.print_hub_title(hub)
                else:
                    print(f'checking emoji in {hub_title}...', end='')
                self.check_emojis()
        self.summary.add_results('emoji', self.emojis)
        print()
