#!/usr/bin/env python3

'Verify links in documentation markdown files.'

import os
import string
from util import versions
from util import walk


def extend_index(full, index):
    'extend the search index if more than one "(" is found before ")"'
    if '(' in full[(index + 2):]:
        index += 2
        open_index = full.index('(', index)
        try:
            close_index = full.index(')', index)
        except ValueError:
            print('missing close in search length:')
            print(repr(full))
            print(f'{" " * index}{"^" * (len(full) - index)}')
            return index
        if open_index < close_index:
            ignore_index = open_index + 1
            if len(full[ignore_index:].split(')')) > 2:
                index = full.index(')', ignore_index) + 1
    return index


def parse_link(full):
    '[text](link) -> text, link, "link" or ![text](link) -> text, link, "image"'
    text_start = full.index('[') + 1
    text_end = full.index(']')
    text = full[text_start:text_end]

    link_start = full.index('(', text_end) + 1
    index = extend_index(full, link_start)
    link_end = full.index(')', index)
    link = full[link_start:link_end]

    identifier = full[full.index('[') - 1]
    link_type = {
        '!': 'image',
        'i': 'iframe',
        's': 'source',
        'x': 'script',
    }.get(identifier, 'link')
    return {'text': text, 'link': link, 'type': link_type}


def get_link_relation(link):
    'determine link relation'
    if link.startswith('http') or link.startswith('//cdn.'):
        return 'http'
    if link.startswith('mailto:') or link.startswith('localhost:'):
        return 'other'
    return 'relative'


def get_sections(section_index, root, filename, link):
    'get headers in markdown file from section index'
    slug = link.split('#')[0] or filename
    path = os.sep.join([root, slug])
    return section_index.get(os.path.realpath(path), [])


def get_section_link(header_text):
    'get a section link string from section header text'
    section = header_text.strip().lower().replace(' ', '-')
    removed_punctuation = string.punctuation.replace('-', '')
    for character in removed_punctuation:
        section = section.replace(character, '')
    return section


def get_files(root, link):
    'get available files at path'
    path = os.sep.join([root, link.split('#')[0]])
    dir_path = os.path.dirname(path)
    if not os.path.exists(dir_path):
        return f'DIR NOT FOUND (\'{dir_path}\')'
    return os.listdir(dir_path)


def is_not_found(**kwargs):
    'check if a link path exists'
    root = kwargs['root']
    full_link = kwargs['link']
    path = os.sep.join([root, full_link.split('#')[0]])
    relative = get_link_relation(full_link) == 'relative'
    return relative and not os.path.exists(path)


def is_doc_link(**kwargs):
    'check if a link is a doc: link'
    link = kwargs['link']
    return link.startswith('doc:')


def is_same_hub(**kwargs):
    'check if a link uses an external url for an internal documentation page'
    link = kwargs['link'].lower()
    current_hub = kwargs['current_hub']
    http = 'http' in link
    farmbot = 'farm.bot' in link
    has_hub = http and link.split('/')[2].startswith(current_hub[:3])
    top_link = link.endswith('farm.bot')
    last = link.split('/')[-1]
    second_to_last = link.split('/')[-2] if len(link.split('/')) > 1 else ''
    version_link = walk.is_version_name(last) and second_to_last == 'docs'
    return http and farmbot and has_hub and not top_link and not version_link


def is_section_missing(**kwargs):
    'check if linked section exists'
    root = kwargs['root']
    filename = kwargs['filename']
    full_link = kwargs['link']
    section_index = kwargs['section_index']
    try:
        section = full_link.split('#')[1]
    except IndexError:
        section = None
    path = os.sep.join([root, full_link.split('#')[0]])
    if os.path.exists(path) and section is not None:
        indexed = get_sections(section_index, root, filename, full_link)
        return not section in indexed
    return False


POSSIBLE_ISSUES = {
    'not_found': {
        'label': 'path not found',
        'check': is_not_found,
    },
    'doc:': {
        'label': 'uses doc:',
        'check': is_doc_link,
    },
    'self': {
        'label': 'uses an external link to its own hub',
        'check': is_same_hub,
    },
    'section_missing': {
        'label': 'section missing in linked file',
        'check': is_section_missing,
    },
    'syntax_error': {'label': 'syntax error', 'check': lambda **_: False}
}


def check_line(**kwargs):
    'verify links in line'
    line = kwargs['line']
    search_string = kwargs['search_string']
    link_count = len(line.split(search_string)) - 1
    visited = []
    while len(visited) < link_count:
        if search_string in line:
            start_index = visited[-1] if len(visited) > 0 else 0
            link_start = line.index(search_string, start_index) + 1
            visited.append(link_start)
            try:
                start = line.rindex('[', 0, link_start)
            except ValueError:
                print('invalid syntax: ', line)
                kwargs['add_syntax_error'](**kwargs)
                continue
            if line[start - 1] == '!':
                start -= 1
            text_end = line.index(']', start)
            text_end = extend_index(line, text_end)
            end = line.index(')', text_end) + 1
            kwargs['check_link'](
                kwargs['root'],
                kwargs['filename'],
                line[start:end],
                kwargs['line_number'])


def check_line_html(**kwargs):
    'verify links in line'
    line = kwargs['line']
    search_string = kwargs['search_string']
    link_count = len(line.split(search_string)) - 1
    visited = []
    while len(visited) < link_count:
        if search_string in line:
            start_index = visited[-1] if len(visited) > 0 else 0
            start = line.index(search_string, start_index) + len(search_string)
            visited.append(start)
            tag_start = line.rindex('<', 0, start) + 1
            tag_end = line.index(' ', tag_start)
            tag = line[tag_start:tag_end]
            identifier = {
                'a': '',
                'iframe': 'i',
                'img': '!',
                'source': 's',
                'script': 'x',
            }[tag]
            end = line.index('"', start)
            link = line[start:end]
            if link.startswith('./dist'):
                continue
            kwargs['check_link'](
                kwargs['root'],
                kwargs['filename'],
                f'{identifier}[]({link})',
                kwargs['line_number'],
                html_line=kwargs['line'].strip('\n'))


class LinkChecker():
    'Check links in documentation. (default directory: current)'

    def __init__(self, summary, folder=None):
        self.summary = summary
        self.verbose = False
        self.folder = folder or '.'
        self.current_hub = None
        self.current_hub_path = None
        self.links = {}
        self.section_index = {}

    def _allow_missing_sections(self, root, issues):
        stable = versions.stable_version_lookup().get(self.current_hub)

        def _allow(issue):
            unstable_version = (stable is not None
                                and versions.get_version_from_root(root) not in stable)
            return unstable_version and issue == 'section_missing'
        return [issue for issue in issues if not _allow(issue)]

    @staticmethod
    def _get_local_path(local_root, filename, link):
        if get_link_relation(link['link']) != 'relative':
            return None
        relative_path = link['link'].split('#')[0]
        if relative_path == '':
            relative_path = filename
        local_path = os.path.realpath(os.sep.join([local_root, relative_path]))
        return local_path.split(os.path.realpath('.'))[1].strip('/')

    def check_link(self, root, filename, full, line_number, html_line=None):
        'verify integrity of link'
        local_root = walk.get_local_root(self.folder, root)
        link = parse_link(full)
        link_check_kwargs = {
            'root': root,
            'filename': filename,
            'link': link['link'],
            'current_hub': self.current_hub,
            'section_index': self.section_index[self.current_hub],
        }
        issues = []
        for issue, issue_data in POSSIBLE_ISSUES.items():
            if issue_data['check'](**link_check_kwargs):
                issues.append(issue)
        status = 'ok'
        problems = self._allow_missing_sections(root, issues)
        if len(problems) > 0:
            status = POSSIBLE_ISSUES[problems[0]]['label']
        link_info = {
            'status': status,
            'type': link['type'],
            'link': get_link_relation(link['link']),
            'version': versions.get_version_from_root(local_root, index=0),
            'from': os.sep.join([local_root, filename]),
            'line_number': line_number,
            'to': link['link'],
            'to_absolute': self._get_local_path(local_root, filename, link),
            'text': link['text'],
            'full': html_line or full,
            'issues': issues,
            'available-sections': get_sections(
                link_check_kwargs['section_index'],
                root, filename, link['link']
            ) if 'section_missing' in issues else None,
            'available-files': get_files(
                root, link['link']
            ) if 'not_found' in issues else None,
        }
        self.links[self.current_hub].append(link_info)
        if self.verbose:
            icon = 'X' if len(issues) > 0 else '|'
            print(f'{icon}{walk.get_indent(local_root) * 3}{link["link"]}')

    def index_sections(self):
        'generate an index of markdown headers in directory files'
        def _parse_lines(root, filename, lines):
            for line in lines:
                for i in range(1, 4):
                    section_prefix = '#' * i + ' '
                    if line.startswith(section_prefix):
                        filepath = os.sep.join([root, filename])
                        file_key = os.path.realpath(filepath)
                        header_text = line.split(section_prefix)[1].strip()
                        section = get_section_link(header_text)
                        hub = self.current_hub
                        existing = self.section_index[hub].get(file_key, [])
                        self.section_index[hub][file_key] = existing + [section]
        path = self.current_hub_path
        walk.walk_through_files(self.folder, path, _parse_lines,
                                self.verbose, quiet=True)

    def add_syntax_error(self, **kwargs):
        'add link syntax error'
        local_root = walk.get_local_root(self.folder, kwargs['root'])
        self.links[self.current_hub].append({
            'status': 'syntax error',
            'type': 'unknown',
            'link': 'unknown',
            'version': versions.get_version_from_root(local_root, index=0),
            'from': os.sep.join([local_root, kwargs['filename']]),
            'line_number': kwargs['line_number'],
            'to': 'unknown',
            'to_absolute': 'unknown',
            'text': 'unknown',
            'full': kwargs['line'].strip('\n'),
            'issues': ['syntax_error'],
            'line': kwargs['line'],
        })

    def check_links(self):
        'verify integrity of links in a directory'
        def _parse_lines(root, filename, lines):
            for line_number, line in enumerate(lines):
                line_check_kwargs = {
                    'check_link': self.check_link,
                    'filename': filename,
                    'root': root,
                    'line': line,
                    'line_number': line_number,
                    'search_string': '](',
                    'add_syntax_error': self.add_syntax_error,
                }
                check_line(**line_check_kwargs)
                for search_string in ['src="', 'href="']:
                    line_check_kwargs['search_string'] = search_string
                    check_line_html(**line_check_kwargs)
        path = self.current_hub_path
        walk.walk_through_files(self.folder, path, _parse_lines, self.verbose)

    def check_all(self, hubs=None):
        'check links in all hubs'
        if hubs is None:
            hubs = versions.HUBS
        for hub in hubs:
            self.current_hub = hub
            self.section_index[hub] = {}
            self.links[hub] = []
            hub_title = f'farmbot-{hub}'
            self.current_hub_path = f'{self.folder}/{hub_title}'
            if os.path.exists(self.current_hub_path):
                if self.verbose:
                    walk.print_hub_title(hub)
                else:
                    print(f'checking links in {hub_title}...', end='')
                self.index_sections()
                self.check_links()
        self.summary.add_results('links', self.links)
        print()
