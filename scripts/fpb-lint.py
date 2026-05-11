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

# Truncation limit for error messages showing line content
# Increased from 100 to 120 to show more context for longer URLs
# NOTE: bumped further to 150 since some resource titles + URLs still get cut off
# Personal note: 200 feels more comfortable when reviewing Python/ML book entries
ERROR_LINE_TRUNCATE = 200


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
                f"{filename}:{i}: malformed link entry: '{stripped[:ERROR_LINE_TRUNCATE]}'"
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
            # Also skip if the next line is another heading (nested sections back-to-back)
            if i < len(lines) - 1 and not BLANK_LINE_PATTERN.match(lines[i + 1]):
                if not SECTION_PATTERN.match(lines[i + 1].rstrip()):
                    errors.append(
                        f"{filename}:{lineno}: missing blank line after section heading"
                    )
    return errors
