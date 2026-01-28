#!/usr/bin/env python3

import argparse
import os
import re
import sys
from dataclasses import dataclass
from typing import Optional, Tuple


FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)\n]+)\)(\{[^}]*\})?")


@dataclass
class FrontMatter:
    raw: str
    body: str
    title: Optional[str]
    cover: Optional[str]


def _strip_yaml_scalar(value: str) -> str:
    v = value.strip()
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        return v[1:-1]
    return v


def parse_front_matter(text: str) -> FrontMatter:
    m = FRONT_MATTER_RE.search(text)
    if not m:
        raise ValueError("front matter missing")

    raw_block = m.group(0)
    attrs = m.group(1)
    body = text[m.end() :]

    title = None
    cover = None

    for line in attrs.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, rest = line.split(":", 1)
        k = key.strip()
        v = _strip_yaml_scalar(rest)
        if k == "title":
            title = v
        elif k == "cover":
            cover = v

    return FrontMatter(raw=raw_block, body=body, title=title, cover=cover)


def replace_or_insert_cover(front_matter_block: str, new_cover_abs: str) -> str:
    lines = front_matter_block.splitlines(keepends=True)
    if not lines or not lines[0].startswith("---"):
        raise ValueError("invalid front matter")

    cover_line_re = re.compile(r"^cover\s*:")
    title_line_re = re.compile(r"^title\s*:")

    for i, line in enumerate(lines):
        if cover_line_re.match(line):
            lines[i] = f"cover: {new_cover_abs}\n"
            return "".join(lines)

    insert_at = None
    for i, line in enumerate(lines):
        if title_line_re.match(line):
            insert_at = i + 1
            break

    if insert_at is None:
        insert_at = 1

    lines.insert(insert_at, f"cover: {new_cover_abs}\n")
    return "".join(lines)


def resolve_local_path(value: str, base_dir: str) -> str:
    v = value.strip()
    if v.startswith("http://") or v.startswith("https://"):
        raise ValueError(f"remote image url is not allowed: {v}")

    v = _strip_yaml_scalar(v)

    if os.path.isabs(v):
        return os.path.normpath(v)

    return os.path.normpath(os.path.join(base_dir, v))


def file_must_exist(path: str, label: str) -> None:
    if not os.path.exists(path):
        raise FileNotFoundError(f"{label} does not exist: {path}")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"{label} is not a file: {path}")


def find_first_image_ref(body: str) -> Optional[str]:
    for m in IMAGE_RE.finditer(body):
        href = m.group(2).strip()
        if href:
            return href
    return None


def convert_image_refs_to_abs(body: str, base_dir: str) -> Tuple[str, int]:
    replaced = 0

    def _repl(m: re.Match) -> str:
        nonlocal replaced
        alt = m.group(1)
        href = m.group(2)
        attrs = m.group(3) or ""

        abs_path = resolve_local_path(href, base_dir)
        file_must_exist(abs_path, "image")
        replaced += 1
        return f"![{alt}]({abs_path}){attrs}"

    new_body = IMAGE_RE.sub(_repl, body)
    return new_body, replaced


def default_publish_ready_path(article_path: str) -> str:
    base, ext = os.path.splitext(article_path)
    if ext.lower() != ".md":
        return f"{article_path}.publish-ready.md"
    return f"{base}.publish-ready{ext}"


def main() -> int:
    parser = argparse.ArgumentParser(prog="contenthub_publish_prep")
    parser.add_argument("--article", required=True)
    parser.add_argument("--output", default=None)
    parser.add_argument("--auto_cover", action="store_true")
    parser.add_argument("--overwrite", action="store_true")

    args = parser.parse_args()

    article_path = os.path.abspath(args.article)
    if not os.path.exists(article_path):
        print(f"ERROR: article not found: {article_path}", file=sys.stderr)
        return 2

    article_dir = os.path.dirname(article_path)
    output_path = os.path.abspath(args.output) if args.output else default_publish_ready_path(article_path)

    if os.path.exists(output_path) and not args.overwrite:
        print(f"ERROR: output exists (use --overwrite): {output_path}", file=sys.stderr)
        return 2

    with open(article_path, "r", encoding="utf-8") as f:
        content = f.read()

    fm = parse_front_matter(content)

    if not fm.title or not fm.title.strip():
        print("ERROR: front matter 'title' missing or empty", file=sys.stderr)
        return 2

    cover_value = (fm.cover or "").strip()
    if not cover_value:
        if not args.auto_cover:
            print("ERROR: front matter 'cover' missing. Use --auto_cover to infer from first image.", file=sys.stderr)
            return 2
        inferred = find_first_image_ref(fm.body)
        if not inferred:
            print("ERROR: cannot infer cover: no images in body", file=sys.stderr)
            return 2
        cover_value = inferred

    cover_abs = resolve_local_path(cover_value, article_dir)
    file_must_exist(cover_abs, "cover")

    new_front_matter = replace_or_insert_cover(fm.raw, cover_abs)

    new_body, replaced = convert_image_refs_to_abs(fm.body, article_dir)

    publish_ready = new_front_matter + new_body

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(publish_ready)

    print("OK")
    print(f"article: {article_path}")
    print(f"publish_ready: {output_path}")
    print(f"images_converted: {replaced}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
