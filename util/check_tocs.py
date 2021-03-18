#!/usr/bin/env python3

'Verify table of contents entries.'

import os
import yaml
from util import versions


def missing(**kwargs):
    'Check if a ToC page exists.'
    return not os.path.exists(kwargs['filename'])


def title_mismatch(**kwargs):
    'Check if a ToC page title matches the markdown file title.'
    return kwargs['toc_page_title'] != kwargs['md_page_title']


POSSIBLE_ISSUES = {
    'page_missing': {
        'label': 'missing page',
        'check': missing,
    },
    'title_mismatch': {
        'label': 'page title mismatch',
        'check': title_mismatch,
    },
}


class TocChecker():
    'Check documentation table of contents data. (default directory: current)'

    def __init__(self, summary, folder=None):
        self.summary = summary
        self.folder = folder or '.'
        self.current_hub = None
        self.pages = {}

    def _descend(self, path, entry):
        if entry.get('pages') is None:
            return
        for page in entry['pages']:
            if page.get('external') is not None:
                continue
            page_path = os.sep.join([path, page['url']])
            page_filename = page_path + '.md'
            self.check_toc_page(page_filename, page, entry['url'])
            self._descend(page_path, page)

    def check_toc_page(self, page_filename, page_data, section_url):
        'verify toc page'
        try:
            with open(page_filename, 'r') as md_file:
                lines = md_file.readlines()
        except FileNotFoundError:
            md_page_title = ''
        else:
            md_page_title = lines[1].split('title: ')[1].strip().strip('"')
        toc_check_kwargs = {
            'filename': page_filename,
            'toc_page_title': page_data['title'],
            'md_page_title': md_page_title,
            'section': section_url,
        }
        issues = []
        for issue, issue_data in POSSIBLE_ISSUES.items():
            if issue_data['check'](**toc_check_kwargs):
                issues.append(issue)
        status = 'ok'
        problems = [issue for issue in issues if issue != 'title_mismatch']
        if len(problems) > 0:
            status = POSSIBLE_ISSUES[problems[0]]['label']
        toc_page_info = {
            'status': status,
            'version': versions.get_version_from_root(page_filename),
            'page': page_filename,
            'toc_page_title': page_data['title'],
            'md_page_title': md_page_title,
            'section': section_url,
            'issues': issues,
        }
        self.pages[self.current_hub].append(toc_page_info)

    def check_toc(self, hub_dir, toc_dir, toc_filename):
        'verify integrity of toc entries'
        with open(os.path.join(toc_dir, toc_filename), 'r') as toc_file:
            toc_data = yaml.safe_load(toc_file)
        version_number = toc_data['version_number']
        version = f'v{version_number}' if version_number != 'docs' else 'docs'
        print(version, end=' ', flush=True)
        for section in toc_data['contents']:
            section_path = os.sep.join([hub_dir, version, section['url']])
            self._descend(section_path, section)

    def check_all(self, hubs=None):
        'check tocs in all hubs'
        if hubs is None:
            hubs = versions.HUBS
        for hub in hubs:
            self.current_hub = hub
            self.pages[hub] = []
            hub_dir = f'{self.folder}/farmbot-{hub}'
            if os.path.exists(hub_dir):
                print(f'checking ToCs in {hub_dir}...', end='')
                toc_dir = f'{hub_dir}/_data/toc'
                toc_filenames = os.listdir(toc_dir)
                for toc_filename in sorted(toc_filenames):
                    self.check_toc(hub_dir, toc_dir, toc_filename)
                    self.summary.add_results('toc', self.pages)
                print()
        print()
