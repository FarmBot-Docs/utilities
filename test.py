#!/usr/bin/env python3

'Utility tests.'

from util import LinkChecker, EmojiChecker, TocChecker, ImageFileChecker, Summary
from util.check_links import get_section_link
from util.summary import color


def assert_eq(what, result, expected):
    'Assert result equals expected.'
    assert result == expected, f'''
    expected {what} to equal {expected}, but got {result}'''


def check_results(item_key, results, expectations):
    'Check that results equal expectations.'
    def assert_expected(key, result):
        'Assert result equals expectation.'
        assert_eq(key, result, expectations[key])

    assert_expected('hub_count', len(results))
    assert_expected('item_count', len(results['test']))
    assert_expected('items', [p[item_key] for p in results['test']])
    assert_expected('ok_count',
                    len([p for p in results['test'] if p['status'] == 'ok']))
    assert_expected('broken_count',
                    len([p for p in results['test'] if p['status'] != 'ok']))


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

    check_results('to', link_checker.links, {
        'hub_count': 1,
        'item_count': 23,
        'ok_count': 16,
        'broken_count': 7,
        'items': [
            'v1_docs.md',
            '../docs/v1_docs.md#v1-docs',
            '#v1-docs',
            '#section_name',
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
            'missing.jpg',
            'broken image (odd).JPG',
            'https://image.png',
            'https://link',
            'https://test.farm.bot',
            'https://test.farm.bot/docs/v1.0',
            'https://test.farm.bot/page',
        ],
    })


def test_check_links_extras():
    'test functions in check_links.py'
    section_link = get_section_link(' Header 1.2!\n')
    assert_eq('section_link', section_link, 'header-12')


def test_emoji_checker():
    'test EmojiChecker'
    summary = Summary()
    emoji_checker = EmojiChecker(summary, 'test_fixtures')
    emoji_checker.verbose = True
    emoji_checker.check_all(['test'])
    summary.print()

    check_results('emoji', emoji_checker.emojis, {
        'hub_count': 1,
        'item_count': 8,
        'ok_count': 6,
        'broken_count': 2,
        'items': [
            '-1',
            '+1',
            '100',
            'clock1',
            'abc',
            'abcde',
            't-rex',
            'alarm-clock',
        ],
    })

    assert_eq('lines_checked',
              summary.arbitrary_data['test'].get('lines_checked'), 54)
    assert_eq('lines_skipped',
              summary.arbitrary_data['test'].get('lines_skipped'), 2)


def test_toc_checker():
    'test TocChecker'
    summary = Summary()
    toc_checker = TocChecker(summary, 'test_fixtures')
    toc_checker.check_all(['test'])
    summary.print()

    check_results('page', toc_checker.pages, {
        'hub_count': 1,
        'item_count': 3,
        'ok_count': 2,
        'broken_count': 1,
        'items': [
            'test_fixtures/farmbot-test/v1/docs/v1_docs.md',
            'test_fixtures/farmbot-test/v1/docs/v1_docs.md',
            'test_fixtures/farmbot-test/v1/docs/missing_page.md',
        ],
    })

    extra_summary_data = summary.extra_summaries['test'].split('-----\n')
    broken_redirect_summary = extra_summary_data[1]
    missing_redirect_summary = extra_summary_data[2]
    not_in_toc_summary = extra_summary_data[3]
    broken_hover_img_path_summary = extra_summary_data[4]
    broken_part_img_path_summary = extra_summary_data[5]

    broken_redirect_count = broken_redirect_summary.count('.md') / 2
    assert_eq('broken redirect count', broken_redirect_count, 1)

    missing_redirect_count = missing_redirect_summary.count('.md')
    assert_eq('missing redirect count', missing_redirect_count, 3)

    not_in_toc_count = not_in_toc_summary.count('.md')
    assert_eq('not in ToC count', not_in_toc_count, 1)

    broken_path_count = broken_hover_img_path_summary.count('  path: ')
    assert_eq('broken hover image count', broken_path_count, 1)

    broken_part_path_count = broken_part_img_path_summary.count('  path: ')
    assert_eq('broken part image count', broken_part_path_count, 1)


def test_image_file_checker():
    'test ImageFileChecker'
    summary = Summary()
    image_file_checker = ImageFileChecker(summary, 'test_fixtures')
    image_file_checker.check_all(['test'])
    summary.print(['test'])

    assert_eq('unused images',
              summary.arbitrary_data['test'].get('unused_images'), {
                  'v1/bom/folder/_images/one.txt',
              })
    assert_eq('unused images',
              summary.arbitrary_data['test'].get('missing_images'), {
                  'unknown',
                  'v1/docs/broken image (odd).JPG',
                  'v1/docs/doc:page',
                  'v1/docs/missing.jpg',
              })


if __name__ == '__main__':
    test_link_checker()
    test_check_links_extras()
    test_emoji_checker()
    test_toc_checker()
    test_image_file_checker()
    print(color('\nTests complete. (OK / PASS)\n', 'green'))
