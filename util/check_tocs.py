#!/usr/bin/env python3

'Verify table of contents entries.'

import os
import yaml
from util import versions, walk


def missing(**kwargs):
    'Check if a ToC page exists.'
    return not os.path.exists(kwargs['filename'])


def title_mismatch(**kwargs):
    'Check if a ToC page title matches the markdown file title.'
    return kwargs['toc_page_title'] != kwargs['md_page_title']


def redirect_missing(**kwargs):
    'Check if a ToC page has a redirect file.'
    hub_dir = os.sep.join(kwargs['filename'].split('/')[:2])
    hub = versions.get_hub_from_dir(hub_dir)
    version = versions.get_version_from_root(kwargs['filename'])
    if version not in versions.latest_stable_versions(hub):
        return False
    if versions.get_hub_from_dir(hub_dir) == 'oer':
        return False
    redirects_dir = os.path.join(hub_dir, '_redirects')
    filename = kwargs['filename'].split('/')[-1]
    expected_filepath = os.path.join(redirects_dir, filename)
    return not os.path.exists(expected_filepath)


POSSIBLE_ISSUES = {
    'page_missing': {
        'label': 'missing page',
        'check': missing,
    },
    'title_mismatch': {
        'label': 'page title mismatch',
        'check': title_mismatch,
    },
    'redirect_missing': {
        'label': 'missing or renamed redirect',
        'check': redirect_missing,
    },
}

IGNORED_ISSUES = [
    'title_mismatch',
    'redirect_missing',
]


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
        problems = [issue for issue in issues if issue not in IGNORED_ISSUES]
        if len(problems) > 0:
            status = POSSIBLE_ISSUES[problems[0]]['label']
        toc_page_info = {
            'status': status,
            'version': versions.get_version_from_root(page_filename),
            'page': page_filename,
            'slug': page_filename.split('/')[-1].split('.')[0],
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
        hub = versions.get_hub_from_dir(hub_dir)
        version = versions.get_version_string(hub, version_number)
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
                broken_redirects = verify_redirects(hub_dir, self.pages)
                self.summary.add_extra_summary(hub, broken_redirects)
                if '.md' in broken_redirects:
                    pass
                    # self.summary.exit_code = 1
                broken_hover_images, _ = verify_hover_images(hub_dir)
                self.summary.add_extra_summary(hub, broken_hover_images)
                if 'page: ' in broken_hover_images:
                    self.summary.exit_code = 1
                broken_part_images, _ = verify_part_images(hub_dir)
                self.summary.add_extra_summary(hub, broken_part_images)
                if 'path: ' in broken_part_images:
                    self.summary.exit_code = 1
                print()
        print()


def verify_redirects(hub_dir, all_pages):
    'Verify redirect integrity.'
    hub = versions.get_hub_from_dir(hub_dir)
    latest_version_number = (versions.latest_stable_versions(hub) or [1])[-1]
    latest_version = versions.get_version_string(hub, latest_version_number)
    redirect_dir = os.path.join(hub_dir, '_redirects')
    missing_files = ''
    if os.path.exists(redirect_dir):
        redirects = []
        broken_redirect_info = []
        for redirect in os.listdir(redirect_dir):
            redirect_filename = os.path.join(redirect_dir, redirect)
            with open(redirect_filename, 'r') as redirect_file:
                lines = redirect_file.readlines()
            for line in lines:
                if line.startswith('page_path:'):
                    page_path = line.split('page_path:')[1].strip()
                    filepath = os.sep.join([
                        hub_dir, latest_version, page_path]) + '.md'
                    filepath = filepath.replace('//', '/')
                    if not os.path.exists(filepath):
                        info = [filepath, redirect_filename]
                        broken_redirect_info.append(info)
                    redirects.append(filepath)
        if len(broken_redirect_info) > 0:
            missing_files += '\n' + ' broken redirects '.upper().center(50, '-') + '\n'
        for broken_redirect in broken_redirect_info:
            redirect_info = f'{broken_redirect[0]} ({broken_redirect[1]})'
            missing_files += f'  {versions.color(redirect_info, "yellow")}\n'
        missing_files += '\n\n'
    version_dir = os.path.join(hub_dir, latest_version)
    if versions.get_version_from_root(version_dir) != 'docs':
        pages = []
        for root, _dirs, files in sorted(os.walk(version_dir)):
            files = [f for f in files if f.endswith('.md')]
            for filename in files:
                page_filename = os.path.join(root, filename)
                pages.append(page_filename)
        missing_redirects = set(pages) - set(redirects)
        if len(missing_redirects) > 0:
            missing_files += '\n' + ' missing redirects '.upper().center(50, '-') + '\n'
        for missing_redirect in missing_redirects:
            missing_files += f'  {versions.color(missing_redirect, "yellow")}\n'
        missing_files += '\n\n'
        not_in_toc = set(pages) - set([p['page'] for p in all_pages[hub]])
        not_in_toc = [p for p in not_in_toc
                      if 'bom' not in p.split('/') and 'bom.md' not in p.split('/')]
        if len(not_in_toc) > 0:
            missing_files += '\n' + ' pages not in ToC '.upper().center(50, '-') + '\n'
        for page in not_in_toc:
            missing_files += f'  {versions.color(page, "yellow")}\n'
        missing_files += '\n\n'
    return missing_files if '.md' in missing_files else ''


def verify_hover_images(hub_dir):
    'Verify hover image integrity.'
    broken = '\n' + ' broken hover image paths '.upper().center(50, '-') + '\n'
    paths = []
    hov_img_data_dir = f'{hub_dir}/_data/section_images'
    if not os.path.exists(hov_img_data_dir):
        return '', paths
    data_filenames = os.listdir(hov_img_data_dir)
    for data_filename in sorted(data_filenames):
        data_filepath = os.path.join(hov_img_data_dir, data_filename)
        with open(data_filepath, 'r') as data_file:
            hov_img_data = yaml.safe_load(data_file)
        version_number = hov_img_data['version_number']
        hub = versions.get_hub_from_dir(hub_dir)
        version = versions.get_version_string(hub, version_number)
        for page in hov_img_data['data']:
            for item in page['data']:
                relative_path = os.sep.join([version, item['image']])
                paths.append(relative_path)
                img_path = os.sep.join([hub_dir, relative_path])
                if not os.path.exists(img_path):
                    broken += f'  page: {page["page"]}\n'
                    broken += f'  section: {item["section"]}\n'
                    broken += f'  path: {versions.color(img_path)}\n\n'
    return broken if 'page: ' in broken else '', paths


def verify_part_images(hub_dir):
    'Verify part image integrity.'
    broken = '\n' + ' broken part image paths '.upper().center(50, '-') + '\n'
    paths = []
    part_img_data_dir = f'{hub_dir}/_data/part_hover_images'
    if not os.path.exists(part_img_data_dir):
        return '', paths
    data_filenames = os.listdir(part_img_data_dir)
    for data_filename in sorted(data_filenames):
        data_filepath = os.path.join(part_img_data_dir, data_filename)
        with open(data_filepath, 'r') as data_file:
            part_img_data = yaml.safe_load(data_file)
        version_number = part_img_data['version_number']
        hub = versions.get_hub_from_dir(hub_dir)
        version = versions.get_version_string(hub, version_number)
        for page in part_img_data['bom']:
            for item in page['parts']:
                relative_path = os.sep.join([version,
                                             'bom', page['category'],
                                             '_images', item['image']])
                paths.append(relative_path)
                img_path = os.sep.join([hub_dir, relative_path])
                if not os.path.exists(img_path):
                    broken += f'  page: {page["category"]}\n'
                    broken += f'  path: {versions.color(img_path)}\n\n'
    return broken if 'path: ' in broken else '', paths
