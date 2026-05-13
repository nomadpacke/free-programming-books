#!/usr/bin/env python3
"""
fpb-lint.py - Linting tool for free-programming-books markdown files.

Checks for:
  - Trailing whitespace
  - Duplicate links
  - Malformed link format
  - Incorrect section spacing
  - Missing or malformed entry formatting

Note: This is a personal fork. I added a fix for the truncated check_section_spacing
function which was cut off mid-comment.
"""

import re
import sys
import argparse
from pathlib import Path
from collections import defaultdict

# Regex patterns
LINK_PATTERN = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
ENTRY_PATTERN = re.compile(
    r'^\* \[.+\]\(.+\)'
    r'(?: - .+)?'
    r'(?: \((.+)\))?$'
)
SECTION_HEADER_PATTERN = re.compile(r'^#{1,4} .+')


def check_trailing_whitespace(lines: list[str], filename: str) -> list[str]:
    """Check for trailing whitespace on each line."""
    errors = []
    for i, line in enumerate(lines, 1):
        if line.rstrip('\n') != line.rstrip():
            errors.append(f"{filename}:{i}: trailing whitespace detected")
    return errors


def check_duplicate_links(lines: list[str], filename: str) -> list[str]:
    """Check for duplicate URLs within the file."""
    errors = []
    seen_urls = defaultdict(list)

    for i, line in enumerate(lines, 1):
        for match in LINK_PATTERN.finditer(line):
            url = match.group(2).strip()
            seen_urls[url].append(i)

    for url, line_numbers in seen_urls.items():
        if len(line_numbers) > 1:
            lines_str = ', '.join(map(str, line_numbers))
            errors.append(
                f"{filename}: duplicate URL '{url}' found on lines {lines_str}"
            )
    return errors


def check_link_format(lines: list[str], filename: str) -> list[str]:
    """Check that list entries follow the expected format."""
    errors = []
    for i, line in enumerate(lines, 1):
        stripped = line.rstrip()
        if not stripped.startswith('* '):
            continue
        # Must contain at least one markdown link
        if not LINK_PATTERN.search(stripped):
            errors.append(
                f"{filename}:{i}: list entry missing valid markdown link: {stripped!r}"
            )
        # Check for bare URLs (not wrapped in markdown link syntax)
        bare_url = re.search(r'(?<!\()https?://[^\s)]+(?!\))', stripped)
        if bare_url:
            errors.append(
                f"{filename}:{i}: bare URL found, should be formatted as [title](url): {stripped!r}"
            )
    return errors


def check_section_spacing(lines: list[str], filename: str) -> list[str]:
    """Check that section headers have blank lines before and after them."""
    errors = []
    for i, line in enumerate(lines):
        stripped = line.rstrip()
        if not SECTION_HEADER_PATTERN.match(stripped):
            continue
        lineno = i + 1
        # Check blank line before header (skip if it's the first line)
        if i > 0 and lines[i - 1].strip() != '':
            errors.append(
                f"{filename}:{lineno}: missing blank line before section header"
            )
        # Check blank line after header (skip if it's the last line)
        # Note: some files end with a header, so we guard against index out of range
        if i < len(lines) - 1 and lines[i + 1].strip() != '':
            errors.append(
                f"{filename}:{lineno}: missing blank line after section header"
            )
    return errors


def lint_file(filepath: Path) -> list[str]:
    """Run all lint checks on a single file."""
    lines = filepath.read_text(encoding='utf-8').splitlines(keepends=True)
    filename = str(filepath)
    errors = []
    errors.extend(check_trailing_whitespace(lines, filename))
    errors.extend(check_duplicate_links(lines, filename))
    errors.extend(check_link_format(lines, filename))
    errors.extend(check_section_spacing(lines, filename))
    return errors


def main():
    parser = argparse.ArgumentParser(
        description='Lint free-programming-books markdown files.'
    )
    parser.add_argument(
        'files',
        nargs='+',
        type=Path,
        help='Markdown files to lint'
    )
    # Personal preference: default to quiet mode so only errors are printed
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        default=False,
        help='Print filenames even when no errors are found'
    )
    args = parser.parse_args()

    all_errors = []
    for filepath in args.files:
        if not filepath.exists():
            print(f"Warning: {filepath} does not exist, skipping.", file=sys.stderr)
            continue
        errors = lint_file(filepath)
        all_errors.extend(errors)
        if args.verbose and not errors:
            print(f"{filepath}: OK")

    for error in all_errors:
        print(error)

    sys.exit(1 if all_errors else 0)


if __name__ == '__main__':
    main()
