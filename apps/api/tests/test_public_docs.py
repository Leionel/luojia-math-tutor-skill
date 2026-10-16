"""Public documentation must not depend on archived local development files."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('check_docs', ROOT / 'scripts/check_docs.py')
docs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(docs)


def test_public_entry_points_resolve():
    assert docs.main() is False


def test_links_preserve_spaces_unicode_and_repeated_headings(tmp_path):
    (tmp_path / '内容 页.md').write_text('# 条件与范围\n# 条件与范围\n', encoding='utf-8')
    page = tmp_path / 'README.md'
    page.write_text('[条件](<内容 页.md#条件与范围-1>)\n[重复](%E5%86%85%E5%AE%B9%20%E9%A1%B5.md#条件与范围)', encoding='utf-8')
    assert docs.check_file(page, tmp_path) == []
    page.write_text('[坏锚点](<内容 页.md#不存在>)', encoding='utf-8')
    assert 'missing heading' in docs.check_file(page, tmp_path)[0]


def test_examples_external_links_and_private_dependencies(tmp_path):
    (tmp_path / 'planning').mkdir()
    (tmp_path / 'planning/private.md').write_text('# 本地', encoding='utf-8')
    page = tmp_path / 'README.md'
    page.write_text('```md\n[示例](missing.md)\n```\n`[示例](missing.md)`\n[外部](https://example.org)\n[本地](planning/private.md)\n[丢失](missing.md)', encoding='utf-8')
    errors = docs.check_file(page, tmp_path)
    assert len(errors) == 2
    assert 'private' in errors[0] and 'missing target' in errors[1]
