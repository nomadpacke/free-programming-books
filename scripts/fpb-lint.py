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
        # personally I find it cleaner to warn on this rather than silently ignore it
        if i < len(lines) - 1 and lines[i + 1].strip() != '':
            errors.append(
                f"{filename}:{lineno}: missing blank line after section header"
            )
    return errors
