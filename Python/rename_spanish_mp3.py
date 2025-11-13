#!/usr/bin/env python3
"""
rename_mp3s.py

Heuristic batch renamer for noisy mp3 filenames.
Default: dry-run (prints proposed renames).
Use --apply to actually perform renames.
Creates a CSV mapping file (rename_map.csv).
"""

import re
import argparse
from pathlib import Path
import csv

# === Config ===
EXTENSIONS = {'.mp3', '.m4a', '.wav', '.aac'}  # will handle common audio extensions
MAP_CSV = 'rename_map.csv'

# === Helpers ===
# Emoji ranges (common ranges) for removal
EMOJI_PATTERN = re.compile(
    '['
    '\U0001F300-\U0001F5FF'
    '\U0001F600-\U0001F64F'
    '\U0001F680-\U0001F6FF'
    '\U0001F700-\U0001F77F'
    '\U0001F780-\U0001F7FF'
    '\U0001F800-\U0001F8FF'
    '\U0001F900-\U0001F9FF'
    '\U0001FA00-\U0001FA6F'
    '\U0001FA70-\U0001FAFF'
    '\u2600-\u26FF'
    '\u2700-\u27BF'
    ']+', flags=re.UNICODE)

# add this helper near the other cleaning functions
def remove_known_tags(s: str) -> str:
    # always remove known repetitive strings (case-insensitive)
    s = re.sub(r'how\s*to\s*spanish\s*podcast', '', s, flags=re.IGNORECASE)
    return s


# remove emoji function
def remove_emojis(s: str) -> str:
    return EMOJI_PATTERN.sub('', s)

# remove bracketed/parenthetical tags and codec info
def strip_brackets_and_parentheses(s: str) -> str:
    # remove anything in square brackets anywhere
    s = re.sub(r'\[[^\]]*\]', '', s)
    # remove trailing parenthetical groups like (128kbit_AAC), or any parenthetical at end
    s = re.sub(r'\s*\([^)]*\)\s*$', '', s)
    # remove any leftover parentheses content in middle (optional)
    s = re.sub(r'\([^)]*\)', ' ', s)
    return s

# remove odd leading characters like arrows, clocks, emojis, punctuation
def strip_leading_noise(s: str) -> str:
    # strip leading non-alnum characters and punctuation
    s = re.sub(r'^[^\w\d]+', '', s, flags=re.UNICODE)
    return s

# remove trailing noise (punctuation, extra spaces)
def strip_trailing_noise(s: str) -> str:
    s = re.sub(r'[^\w\d]+$', '', s, flags=re.UNICODE)
    return s

# choose the best segment when filename has separators
def choose_best_segment(segments):
    # score each segment by number of alpha chars and number of title-case words
    def score(seg):
        alpha_count = len(re.findall(r'[A-Za-zÀ-ÖØ-öø-ÿ]', seg))
        title_words = sum(1 for w in re.findall(r"\b\w+\b", seg) if w[0].isupper())
        # penalize segments that look like tags
        tag_penalty = 0
        lower = seg.lower()
        for tag in ('listening', 'spanish', 'audio', 'podcast', 'lecture', 'mp3'):
            if tag in lower:
                tag_penalty += 5
        return alpha_count + title_words * 5 - tag_penalty

    scored = [(score(s), s.strip()) for s in segments]
    scored.sort(reverse=True)
    return scored[0][1] if scored else ''

def sanitize_whitespace_and_punct(s: str) -> str:
    # collapse multiple spaces
    s = re.sub(r'\s+', ' ', s).strip()
    # remove weird leading/trailing punctuation left over
    s = s.strip(" -–—_:;,.")
    return s

def make_safe_filename(s: str) -> str:
    # remove chars not allowed in filenames on many systems
    s = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', s)
    s = s.strip()
    return s

def extract_title(filename_no_ext: str) -> str:
    s = filename_no_ext

    # initial replacements to make splitting easier
    s = s.replace('_', ' ')
    # remove emojis early
    s = remove_emojis(s)
    # remove known repetitive tags
    s = remove_known_tags(s)
    # strip bracketed tags and parentheticals
    s = strip_brackets_and_parentheses(s)
    # strip leading non-alnum noise
    s = strip_leading_noise(s)
    # split heuristics: try common separators
    # common separators: " - ", " — ", ":", "–"
    # split then choose best segment
    if ' - ' in s or ' — ' in s or ' – ' in s or ':' in s:
        # split on multiple separators
        parts = re.split(r'\s[-—–:]\s', s)
        # if only two but left is short and weird, choose right; use choose_best_segment
        best = choose_best_segment(parts)
        s = best
    else:
        # if no clear separator, try to remove leading "SPANISH Listening" style prefixes
        # drop short all-caps leading tokens like "SPANISH", "ENGLISH", etc.
        # if starts with words followed by a space and the first word is all uppercase and short, drop it
        m = re.match(r'^([A-Z]{2,20})(\s+.+)$', s)
        if m:
            candidate = m.group(2).strip()
            # keep candidate only if it seems better (more letters)
            if len(re.findall(r'[A-Za-z]', candidate)) > len(re.findall(r'[A-Za-z]', s)):
                s = candidate

    # remove remaining emojis and stray punctuation
    s = remove_emojis(s)
    s = sanitize_whitespace_and_punct(s)
    s = strip_trailing_noise(s)
    s = make_safe_filename(s)

    # final fallback: if result is empty, use the original cleaned filename
    if not s:
        s = make_safe_filename(filename_no_ext)

    return s

# === Main ===
def main(directory: Path, apply: bool, recursive: bool):
    files = []
    if recursive:
        for p in directory.rglob('*'):
            if p.is_file() and p.suffix.lower() in EXTENSIONS:
                files.append(p)
    else:
        for p in directory.iterdir():
            if p.is_file() and p.suffix.lower() in EXTENSIONS:
                files.append(p)

    mapping = []  # tuples (old_path, new_path)
    seen_new_names = {}  # to avoid duplicates: new_name -> count

    for p in sorted(files):
        stem = p.stem  # filename without extension
        new_title = extract_title(stem)
        new_name = new_title + p.suffix.lower()
        # avoid overwriting existing files in same dir: if name exists, add (1),(2)...
        count = seen_new_names.get(new_name, 0)
        candidate_name = new_name
        while True:
            candidate_path = p.with_name(candidate_name)
            # if candidate_path is same as original file path, it's fine
            if candidate_path.exists() and candidate_path != p:
                # if file exists and is not this file, bump counter
                count += 1
                base = new_title
                candidate_name = f"{base} ({count}){p.suffix.lower()}"
                continue
            # also avoid collisions within our planned mapping
            if any(dst == candidate_path for _, dst in mapping if dst.parent == p.parent and dst != p):
                count += 1
                base = new_title
                candidate_name = f"{base} ({count}){p.suffix.lower()}"
                continue
            break
        seen_new_names[new_name] = count

        dst_path = p.with_name(candidate_name)
        mapping.append((p, dst_path))

    # Print preview
    print(f"Found {len(mapping)} audio files. Preview of renames:\n")
    for src, dst in mapping:
        if src == dst:
            print(f"SKIP (same): {src.name}")
        else:
            print(f"{src.name}  ->  {dst.name}")

    # Save mapping CSV
    with open(MAP_CSV, 'w', newline='', encoding='utf-8') as csvf:
        writer = csv.writer(csvf)
        writer.writerow(['old_path', 'new_path'])
        for src, dst in mapping:
            writer.writerow([str(src), str(dst)])
    print(f"\nMapping saved to {MAP_CSV}")

    if not apply:
        print("\nDry-run complete. No files were changed. Re-run with --apply to rename files.")
        return

    # Perform renames
    renamed = 0
    for src, dst in mapping:
        if src == dst:
            continue
        try:
            src.rename(dst)
            renamed += 1
        except Exception as e:
            print(f"FAILED to rename {src} -> {dst}: {e}")

    print(f"\nRename complete. {renamed} files renamed.")


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Heuristic batch renamer for audio files')
    ap.add_argument('dir', nargs='?', default='.', help='Directory containing files (default: current directory)')
    ap.add_argument('--apply', action='store_true', help='Actually perform the renames (default is dry-run)')
    ap.add_argument('--recursive', action='store_true', help='Process files in subdirectories recursively')
    args = ap.parse_args()

    main(Path(args.dir), apply=args.apply, recursive=args.recursive)
