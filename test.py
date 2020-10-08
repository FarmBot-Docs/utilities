#!/usr/bin/env python3

'Utility tests.'

from util import LinkChecker, EmojiChecker, Summary
from util.check_links import get_section_link


def test_link_checker():
    'test LinkChecker'
    summary = Summary()
    link_checker = LinkChecker(summary, 'test_fixtures')
    link_checker.verbose = True
    link_checker.check_all(['test'])
    kwargs = {
        # 'max_link_issue_print_count': 1,
        # 'max_image_issue_print_count': 1,
        # 'link_issue_filter': 'not_found',
    }
    summary.print(**kwargs)

    results = link_checker.links
    assert len(results) == 1
    assert len(results['test']) == 21
    assert [l['to'] for l in results['test']] == [
        'v1_docs.md',
        '../docs/v1_docs.md#v1-docs',
        '#v1-docs',
        '../docs/v1_docs.md#v2-docs',
        'v1_docs.md',
        '../../v2/docs/v2_docs.md',
        '../docs/v1_docs.md',
        'doc:page',
        'mailto:email',
        'unknown',
        'v1_docs.md',
        'https://',
        'https://',
        'https://',
        'v1_docs.md',
        'broken image (odd).JPG',
        'https://image.png',
        'https://link',
        'https://test.farm.bot',
        'https://test.farm.bot/v1.0',
        'https://test.farm.bot/page',
    ]
    assert len([l for l in results['test'] if l['status'] == 'ok']) == 15
    assert len([l for l in results['test'] if l['status'] != 'ok']) == 6


def test_check_links_extras():
    'test functions in check_links.py'
    assert get_section_link(' Header 1.2!\n') == 'header-12'


def test_emoji_checker():
    'test EmojiChecker'
    summary = Summary()
    emoji_checker = EmojiChecker(summary, 'test_fixtures')
    emoji_checker.verbose = True
    emoji_checker.check_all(['test'])
    summary.print()

    results = emoji_checker.emojis
    assert len(results) == 1
    assert len(results['test']) == 8
    assert [e['emoji'] for e in results['test']] == [
        '-1',
        '+1',
        '100',
        'clock1',
        'abc',
        'abcde',
        't-rex',
        'alarm-clock',
    ]
    assert len([e for e in results['test'] if e['status'] == 'ok']) == 6
    assert len([e for e in results['test'] if e['status'] != 'ok']) == 2


if __name__ == '__main__':
    test_link_checker()
    test_check_links_extras()
    test_emoji_checker()
    print('\ntests complete: ok\n')
