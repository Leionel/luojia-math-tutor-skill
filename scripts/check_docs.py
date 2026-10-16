"""Check local links in maintained public documentation without network access."""
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
ENTRIES = ('README.md', 'AGENTS.md', 'evaluation/r2/README.md',
           'evaluation/s5/README.md', 'evaluation/math-feedback-boundaries.md')
PRIVATE = {'planning', '.local', 'superpowers', 'screenshots', 'ui-proposals'}


def prose(text):
    lines = []
    fence = None
    for line in text.splitlines():
        marker = re.match(r'^\s{0,3}(`{3,}|~{3,})', line)
        if marker:
            token = marker[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence is None:
            lines.append(line)
    return '\n'.join(lines)


def anchors(text):
    result, counts = set(), {}
    for heading in re.findall(r'^\s{0,3}#{1,6}\s+(.+?)\s*#*$', prose(text), re.M):
        heading = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', heading)
        slug = re.sub(r'[^\w\- ]', '', heading.lower()).replace(' ', '-')
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        result.add(f'{slug}-{count}' if count else slug)
    return result


def check_file(path, root=ROOT):
    text = prose(path.read_text(encoding='utf-8'))
    # Inline-code examples are not links. Reference definitions are checked too.
    text = re.sub(r'`+[^`\n]*`+', '', text)
    links = re.findall(r'!?\[[^\]\n]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+[^)]*)?\)', text)
    links += re.findall(r'^\s{0,3}\[[^\]]+\]:\s*(<[^>]+>|\S+)', text, re.M)
    errors = []
    for raw in links:
        url = urlsplit(raw.strip('<>'))
        if url.scheme or url.netloc:
            continue
        target = (path.parent / unquote(url.path)).resolve() if url.path else path.resolve()
        label = f'{path.relative_to(root)}: {raw}'
        if not target.is_relative_to(root):
            errors.append(label + ' escapes repository')
        elif set(target.relative_to(root).parts) & PRIVATE:
            errors.append(label + ' depends on private development material')
        elif not target.exists():
            errors.append(label + ' missing target')
        elif url.fragment and target.suffix == '.md' and unquote(url.fragment) not in anchors(target.read_text(encoding='utf-8')):
            errors.append(label + ' missing heading anchor')
    return errors


def main():
    files = [ROOT / p for p in ENTRIES] + sorted((ROOT / 'docs').glob('*.md'))
    errors = [error for path in files for error in check_file(path)]
    for error in errors:
        print(error)
    print(f'Public documentation: {len(files)} files, {len(errors)} broken local links')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
