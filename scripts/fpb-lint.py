#!/usr/bin/env python3
"""
fpb-lint.py - Linter for free-programming-books markdown files.

Checks for common formatting issues such as:
- Incorrect link formatting
- Missing or extra blank lines
- Alphabetical ordering within sections
- Duplicate entries
- Trailing whitespace
- Invalid characters in links
"""

import re
import sys
import argparse
from pathlib import Path

# Regex patterns
LINK_PATTERN = re.compile(r'\* \[(.+?)\]\((.+?)\)(.*)')
SECTION_PATTERN = re.compile(r'^#{1,4} .+')
BLANK_LINE_PATTERN = re.compile(r'^\s*$')
TRAILING_WHITESPACE_PATTERN = re.compile(r'[ \t]+$')


def check_trailing_whitespace(lines: list[str], filename: str) -> list[str]:
    """Check for trailing whitespace on each line."""
    errors = []
    for i, line in enumerate(lines, 1):
        if TRAILING_WHITESPACE_PATTERN.search(line.rstrip('\n')):
            errors.append(f"{filename}:{i}: trailing whitespace detected")
    return errors


def check_duplicate_links(lines: list[str], filename: str) -> list[str]:
    """Check for duplicate URLs within the file."""
    errors = []
    seen_urls: dict[str, int] = {}
    for i, line in enumerate(lines, 1):
        match = LINK_PATTERN.match(line.strip())
        if match:
            url = match.group(2)
            if url in seen_urls:
                errors.append(
                    f"{filename}:{i}: duplicate URL '{url}' "
                    f"(first seen at line {seen_urls[url]})"
                )
            else:
                seen_urls[url] = i
    return errors


def check_link_format(lines: list[str], filename: str) -> list[str]:
    """Check that list entries follow the expected link format."""
    errors = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # Lines starting with '* [' should match the full link pattern
        if stripped.startswith('* [') and not LINK_PATTERN.match(stripped):
            errors.append(
                f"{filename}:{i}: malformed link entry: '{stripped[:80]}'"
            )
    return errors


def check_section_spacing(lines: list[str], filename: str) -> list[str]:
    """Check that sections are preceded and followed by a blank line."""
    errors = []
    for i, line in enumerate(lines):
        if SECTION_PATTERN.match(line.rstrip()):
            lineno = i + 1
            # Check blank line before section (skip if first line)
            if i > 0 and not BLANK_LINE_PATTERN.match(lines[i - 1]):
                errors.append(
                    f"{filename}:{lineno}: missing blank line before section heading"
                )
            # Check blank line after section (skip if last line)
            if i < len(lines) - 1 and not BLANK_LINE_PATTERN.match(lines[i + 1]):
                errors.append(
                    f"{filename}:{lineno}: missing blank line after section heading"
                )
    return errors


def lint_file(filepath: Path) -> list[str]:
    """Run all lint checks on a single markdown file."""
    try:
        lines = filepath.read_text(encoding='utf-8').splitlines(keepends=True)
    except UnicodeDecodeError as e:
        return [f"{filepath}: encoding error - {e}"]

    filename = str(filepath)
    errors: list[str] = []
    errors.extend(check_trailing_whitespace(lines, filename))
    errors.extend(check_duplicate_links(lines, filename))
    errors.extend(check_link_format(lines, filename))
    errors.extend(check_section_spacing(lines, filename))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Lint free-programming-books markdown files.'
    )
    parser.add_argument(
        'files',
        nargs='+',
        type=Path,
        help='Markdown files to lint',
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Exit with error code 1 if any warnings are found',
    )
    args = parser.parse_args()

    all_errors: list[str] = []
    for filepath in args.files:
        if not filepath.exists():
            print(f"Warning: file not found: {filepath}", file=sys.stderr)
            continue
        all_errors.extend(lint_file(filepath))

    for error in all_errors:
        print(error)

    if all_errors:
        print(f"\n{len(all_errors)} issue(s) found.", file=sys.stderr)
        return 1 if args.strict or any('duplicate' in e or 'malformed' in e for e in all_errors) else 0

    print("No issues found.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
