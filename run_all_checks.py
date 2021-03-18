#!/usr/bin/env python3

'Run all documentation file checks.'

import sys
from util import LinkChecker, EmojiChecker, TocChecker, ImageFileChecker, Summary

if __name__ == '__main__':
    summary = Summary()

    for Checker in [TocChecker, EmojiChecker, LinkChecker, ImageFileChecker]:
        checker = Checker(summary)
        checker.check_all()

    summary.print()
    sys.exit(summary.exit_code)
