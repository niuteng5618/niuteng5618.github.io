#!/usr/bin/env python3
"""为 _posts/ 全部文章计算并写入 word_count / reading_time front matter 字段。

字数 = 正文中文字符数 + 英文单词数
       （剔除代码块、行内代码、HTML 标签、图片、链接语法、Markdown 结构符号）
阅读时间 = ceil(字数 / 400) 分钟，最少 1 分钟

幂等：重复运行会覆盖旧值。导入新文章后运行一次即可。

用法:
    python3 _scripts/update_reading_stats.py [文件...]   # 缺省处理 _posts/ 全部文章
"""
import math
import re
import sys
from pathlib import Path

POSTS_DIR = Path(__file__).resolve().parent.parent / "_posts"
CHARS_PER_MINUTE = 400

FENCE = re.compile(r"```.*?```", re.S)
INDENTED_CODE = re.compile(r"(?m)^(?:    |\t).*$")
INLINE_CODE = re.compile(r"`[^`\n]*`")
MD_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
MD_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
HTML_TAG = re.compile(r"<[^>]+>")
MD_SYNTAX = re.compile(r"[#>*_~|\-]+")
CJK = re.compile(r"[㐀-䶿一-鿿豈-﫿]")
WORD = re.compile(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)*")


def count_words(body: str) -> int:
    body = FENCE.sub(" ", body)
    body = INDENTED_CODE.sub(" ", body)
    body = INLINE_CODE.sub(" ", body)
    body = MD_IMAGE.sub(" ", body)
    body = MD_LINK.sub(r"\1", body)
    body = HTML_TAG.sub(" ", body)
    body = MD_SYNTAX.sub(" ", body)
    return len(CJK.findall(body)) + len(WORD.findall(body))


def update_post(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        print(f"SKIP (no front matter): {path.name}")
        return False
    fm, body = m.group(1), text[m.end():]

    words = count_words(body)
    minutes = max(1, math.ceil(words / CHARS_PER_MINUTE))

    lines = [ln for ln in fm.split("\n") if not re.match(r"^(word_count|reading_time):", ln)]
    # 插在 toc 行之后；没有 toc 就插在 front matter 末尾
    insert_at = next((i + 1 for i, ln in enumerate(lines) if ln.startswith("toc:")), len(lines))
    lines[insert_at:insert_at] = [f"word_count: {words}", f"reading_time: {minutes}"]

    new_text = "---\n" + "\n".join(lines) + "\n---\n" + body
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
        print(f"OK   {path.name}: {words} 字 / {minutes} 分钟")
        return True
    print(f"KEEP {path.name}: {words} 字 / {minutes} 分钟 (无变化)")
    return False


def main() -> None:
    args = sys.argv[1:]
    paths = [Path(a) for a in args] if args else sorted(POSTS_DIR.glob("*.md"))
    changed = sum(update_post(p) for p in paths)
    print(f"\n共 {len(paths)} 篇，更新 {changed} 篇")


if __name__ == "__main__":
    main()
