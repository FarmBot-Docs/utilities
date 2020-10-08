#!/usr/bin/env python3

'Run all documentation file checks.'

import sys
from util import LinkChecker, EmojiChecker, Summary

if __name__ == '__main__':
    summary = Summary()

    link_checker = LinkChecker(summary)
    link_checker.check_all()

    emoji_checker = EmojiChecker(summary)
    emoji_checker.check_all()

    summary.print()
    sys.exit(summary.exit_code)
