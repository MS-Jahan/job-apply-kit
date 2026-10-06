#!/usr/bin/env python3
"""
Count rendered characters in LaTeX resume/CV bullets.
Strips LaTeX markup to show what a reader actually sees on the page.

Usage:
  python3 char_count.py "\\textbf{DFT} analysis of \\ce{TiO2} surfaces"
  echo "bullet text" | python3 char_count.py
  python3 char_count.py -f cv output/file.tex
  python3 char_count.py --raw "bullet text"              # just the number
"""

import re
import sys
import argparse


def strip_latex(text):
    """Strip LaTeX markup to get rendered text."""
    # Remove \item[] prefix
    text = re.sub(r'\\item\s*(\[\s*\])?\s*', '', text)
    # \href{url}{text} -> text
    text = re.sub(r'\\href\{[^}]*\}\{([^}]*)\}', r'\1', text)
    # \textbf{X} -> X
    text = re.sub(r'\\textbf\{([^}]*)\}', r'\1', text)
    # \textit{X} -> X
    text = re.sub(r'\\textit\{([^}]*)\}', r'\1', text)
    # \underline{X} -> X
    text = re.sub(r'\\underline\{([^}]*)\}', r'\1', text)
    # \emph{X} -> X
    text = re.sub(r'\\emph\{([^}]*)\}', r'\1', text)
    # \ce{X} -> X (subscript digits still count as 1 char each)
    text = re.sub(r'\\ce\{([^}]*)\}', r'\1', text)
    # Greek letters -> 1 char each
    greeks = [
        'alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta', 'eta', 'theta',
        'iota', 'kappa', 'lambda', 'mu', 'nu', 'xi', 'pi', 'rho', 'sigma',
        'tau', 'upsilon', 'phi', 'chi', 'psi', 'omega',
        'Alpha', 'Beta', 'Gamma', 'Delta', 'Theta', 'Lambda', 'Sigma',
        'Phi', 'Psi', 'Omega',
    ]
    for g in greeks:
        text = text.replace(f'$\\{g}$', 'G')
        text = text.replace(f'\\{g}', 'G')
    # $^\circ$ -> 1 char
    text = re.sub(r'\$\^\{?\\circ\}?\$', 'D', text)
    # $^\dagger$ -> 1 char
    text = re.sub(r'\$\^\{?\\dagger\}?\$', 'D', text)
    # Superscripts: $^{2}$ or $^2$ -> content
    text = re.sub(r'\$\^\{([^}]*)\}\$', r'\1', text)
    text = re.sub(r'\$\^(.)\$', r'\1', text)
    # Subscripts: $_{2}$ or $_2$ -> content
    text = re.sub(r'\$_\{([^}]*)\}\$', r'\1', text)
    text = re.sub(r'\$_(.)\$', r'\1', text)
    # \sim -> 1 char (~)
    text = text.replace('$\\sim$', '~')
    text = text.replace('\\sim', '~')
    text = text.replace('\\textasciitilde', '~')
    # $<$ $>$ -> 1 char
    text = re.sub(r'\$([<>])\$', r'\1', text)
    # --- -> em-dash (1 char but ~2x wide)
    text = text.replace('---', '\u2014')
    # -- -> en-dash (1 char)
    text = text.replace('--', '\u2013')
    # Remove remaining $ (math mode delimiters)
    text = text.replace('$', '')
    # Remove remaining \commands
    text = re.sub(r'\\[a-zA-Z]+\s*', '', text)
    # Remove remaining braces
    text = text.replace('{', '').replace('}', '')
    # Collapse multiple spaces
    text = re.sub(r'  +', ' ', text)
    return text.strip()


def count_bold_chars(text):
    """Count characters inside \\textbf{} commands."""
    return sum(len(m) for m in re.findall(r'\\textbf\{([^}]*)\}', text))


def count_em_dashes(text):
    """Count em-dashes (---) which render ~2x wide."""
    return len(re.findall(r'---', text))


def classify_bullet(char_count, bold_chars, fmt):
    """Classify bullet into variant and check limits."""
    if fmt == 'resume':
        base = 119
        penalty = 0.5
        tiers = [
            ('1L', 105, 111, 117, None),
            ('2L', 189, 205, 218, 78),
        ]
    else:
        base = 91
        penalty = 0.25
        tiers = [
            ('1L', 88, 93, 101, None),
            ('2L', 168, 182, 190, 65),
            ('3L', 250, 268, 280, 65),
        ]

    effective = base - (penalty * bold_chars)

    for variant, lo, hi, hard_max, orphan in tiers:
        if char_count <= hard_max:
            if char_count < lo:
                status = 'SHORT'
            elif char_count <= hi:
                status = 'OK'
            else:
                status = 'NEAR MAX'
            return variant, status, lo, hi, hard_max, orphan, effective

    return 'OVER', 'OVER LIMIT', 0, 0, 0, None, effective


def format_one(raw, fmt):
    """Format analysis for a single bullet."""
    rendered = strip_latex(raw)
    n = len(rendered)
    bold = count_bold_chars(raw)
    em = count_em_dashes(raw)

    variant, status, lo, hi, hard_max, orphan, eff = classify_bullet(n, bold, fmt)

    parts = [f"  {n:3d} chars | {variant} {fmt.upper()} | {status} (target {lo}-{hi}, max {hard_max})"]
    if bold:
        parts.append(f"  Bold: {bold} chars -> effective limit/line: {eff:.0f}")
    if em:
        parts.append(f"  Em-dashes: {em} (each ~2x wide, budget +{em} extra)")
    parts.append(f"  Rendered: {rendered}")
    return '\n'.join(parts), variant


def extract_items(text):
    """Extract \\item lines from .tex source."""
    items = []
    for line in text.split('\n'):
        s = line.strip()
        if s.startswith('\\item'):
            items.append(s)
    return items


def main():
    parser = argparse.ArgumentParser(
        description='Count rendered characters in LaTeX resume/CV bullets')
    parser.add_argument('input', nargs='?',
                        help='Bullet text or .tex file path')
    parser.add_argument('-f', '--format', choices=['resume', 'cv'],
                        default='resume', help='Document format (default: resume)')
    parser.add_argument('--raw', action='store_true',
                        help='Output only char count (for scripting)')
    args = parser.parse_args()

    if args.input and args.input.endswith('.tex'):
        with open(args.input) as f:
            items = extract_items(f.read())
        if not items:
            print("No \\item lines found.")
            return
        total_lines = 0
        print(f"Found {len(items)} bullets ({args.format} format):\n")
        for i, item in enumerate(items, 1):
            if args.raw:
                print(len(strip_latex(item)))
            else:
                report, variant = format_one(item, args.format)
                print(f"Bullet {i}:")
                print(report)
                print()
                if variant not in ('OVER',):
                    total_lines += int(variant[0])
        if not args.raw:
            print(f"Total rendered lines: {total_lines}")
    elif args.input:
        if args.raw:
            print(len(strip_latex(args.input)))
        else:
            report, _ = format_one(args.input, args.format)
            print(report)
    else:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            if args.raw:
                print(len(strip_latex(line)))
            else:
                report, _ = format_one(line, args.format)
                print(report)
                print()


if __name__ == '__main__':
    main()
