#!/usr/bin/env python3

'Summarization and result reporting utilities.'

import os
import json
from util.check_links import POSSIBLE_ISSUES as POSSIBLE_LINK_ISSUES
from util.check_emoji import POSSIBLE_ISSUES as POSSIBLE_EMOJI_ISSUES
from util.walk import print_hub_title, get_relative_filename

ORDERED_LINK_INFO_KEYS = ['status', 'type', 'link',
                          'from', 'line_number', 'to', 'text', 'issues']
LINK_ISSUE_KEYS_LOOKUP = {
    'link': {
        'relative': ['not_found', 'doc:', 'section_missing'],
        'http': ['self'],
        'other': [],
    },
    'image': {'relative': ['not_found'], 'http': []},
    'iframe': {'http': []},
    'source': {'http': []},
    'script': {'http': []},
}
ORDERED_LINK_ISSUE_KEYS = [
    'not_found',
    'doc:',
    'self',
    'section_missing',
    'syntax_error',
]


def print_issue_counts(links, link_type=None, relation=None):
    'print link issues counts'
    if link_type is not None:
        links = [l for l in links if l['type'] == link_type]
    if relation is not None:
        links = [l for l in links if l['link'] == relation]
    extensions_string = ''
    if link_type == 'image':
        extension_counts = {}
        for link in links:
            ext = link['to'].split('.')[-1].lower()
            extension_counts[ext] = extension_counts.get(ext, 0) + 1
        extensions_string = f'({extension_counts})'
    sources_string = ''
    if relation == 'http':
        source_count = len({l['to'].split('/')[2] for l in links})
        sources_string = f'({source_count} sites)'
    counts = {k['label']: 0 for k in POSSIBLE_LINK_ISSUES.values()}
    for link in links:
        for issue in link['issues']:
            counts[POSSIBLE_LINK_ISSUES[issue]['label']] += 1
    print()
    if link_type is not None:
        print(f'{link_type or ""}s ({relation or "all"}):')
    try:
        issue_keys = LINK_ISSUE_KEYS_LOOKUP[link_type][relation]
    except KeyError:
        issue_keys = ORDERED_LINK_ISSUE_KEYS
    details = f'{extensions_string} {sources_string}' if len(links) > 0 else ''
    print(f'{len(links):>6} total {details}')
    print('  ----------')
    if len(issue_keys) > 0:
        print(f'{len([l for l in links if len(l["issues"]) == 0]):>6} ok')
    for issue in issue_keys:
        count = counts[POSSIBLE_LINK_ISSUES[issue]['label']]
        print(f'{count:>6} {POSSIBLE_LINK_ISSUES[issue]["label"]}')


def print_link_summary(hub_links, **kwargs):
    'print a summary of verified links'
    print('\n')
    print(' link summary '.upper().center(50, '-'))
    print_issue_counts(hub_links)
    for link_type, relation_issues in LINK_ISSUE_KEYS_LOOKUP.items():
        for link_relation in relation_issues:
            print_issue_counts(hub_links, link_type, link_relation)
    print()
    max_counts = {
        'link': kwargs.get('max_link_issue_print_count'),
        'image': kwargs.get('max_image_issue_print_count'),
    }
    issue_filter = kwargs.get('link_issue_filter')
    print_broken_links(hub_links, max_counts, issue_filter)
    print('\n')


def print_broken_links(hub_links, max_counts, issue_filter):
    'print list of broken link info'
    broken_links = [l for l in hub_links if len(l['issues']) > 0]

    if len(broken_links) > 0:
        print(' broken links '.upper().center(50, '-'))
    print_counts = {'link': 0, 'image': 0}
    for link in broken_links:
        current_count = print_counts.get(link['type'], 0)
        max_count = max_counts.get(link['type'])
        print_link = max_count is None or (current_count < max_count)
        if issue_filter is None and not print_link:
            continue
        if issue_filter is None or (issue_filter in link['issues']):
            if print_link:
                print_counts[link['type']] = current_count + 1
            print()
            extra = []
            for extra_key in ['available-sections', 'line']:
                if link.get(extra_key) is not None:
                    extra.append(extra_key)
            for key in ORDERED_LINK_INFO_KEYS + extra:
                print(f'{key:<12}: {link[key]}')

    def _more(link_type):
        total_filtered = [l for l in broken_links if l['type'] == link_type]
        return len(total_filtered) - print_counts[link_type]
    more_links = _more('link')
    more_images = _more('image')
    if more_links > 0 or more_images > 0:
        print(f'\n+ {more_links} links and {more_images} images not shown')
    if issue_filter is not None:
        print(f'\n(only links with \'{issue_filter}\' issue displayed)')


def print_emoji_summary(hub_emojis, **_kwargs):
    'print a summary of verified emoji'
    print('\n')
    print(' emoji summary '.upper().center(50, '-'))
    unique = {e['emoji'] for e in hub_emojis}
    print(f'{len(hub_emojis):>6} total ({len(unique)} unique)')
    print(f'       {", ".join(unique)}')
    print('  ----------')
    print(f'{len([e for e in hub_emojis if len(e["issues"]) == 0]):>6} ok')
    for issue, issue_data in POSSIBLE_EMOJI_ISSUES.items():
        count = len([e for e in hub_emojis if issue in e["issues"]])
        print(f'{count:>6} {issue_data["label"]}')
    broken_emojis = [e for e in hub_emojis if len(e['issues']) > 0]
    print()
    if len(broken_emojis) > 0:
        print(' broken emojis '.upper().center(50, '-'))
    for emoji in broken_emojis:
        for key in ['status', 'from', 'line_number', 'emoji', 'issues']:
            print(f'{key:<12}: {emoji[key]}')
        print()
    print('\n')


SUMMARY_FOR = {
    'links': print_link_summary,
    'emoji': print_emoji_summary,
}


class Summary():
    'gather and print results summary'

    def __init__(self):
        self.results = {}
        self.exit_code = 0

    def add_results(self, key, data):
        'add results'
        self.results[key] = data
        self.save_results(key)

    def print(self, **kwargs):
        'print summary'
        hub_results = self.results[list(self.results.keys())[0]]
        hubs = [hub for hub, results in hub_results.items() if len(results) > 0]
        for hub in hubs:
            print_hub_title(hub)
            for results_key, results_data in self.results.items():
                SUMMARY_FOR[results_key](results_data[hub], **kwargs)

    def save_results(self, results_key):
        'save results to file'
        results_dir = get_relative_filename('results')
        if not os.path.exists(results_dir):
            os.mkdir(results_dir)

        results = self.results[results_key]
        filename = os.path.join(results_dir, f'{results_key}_results.json')
        with open(filename, 'w') as results_file:
            results_file.write(json.dumps(results, indent=2))

        issues = {}
        for hub, results in results.items():
            issues[hub] = []
            for result in results:
                if result['status'] != 'ok':
                    issues[hub].append(result)
            if len(issues[hub]) > 0:
                self.exit_code = 1
        filename = os.path.join(results_dir, f'{results_key}_issues.json')
        with open(filename, 'w') as results_file:
            results_file.write(json.dumps(issues, indent=2))
