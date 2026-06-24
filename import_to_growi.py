#!/usr/bin/env python3
"""
MarkdownファイルをGROWIに投稿する簡易スクリプトです。

cmdでの実行例:
  set "GROWI_URL=http://localhost:3000"
  set "GROWI_TOKEN=発行したAPIトークン"
  py import_to_growi.py
"""

import os
from pathlib import Path
import requests

GROWI_URL = os.environ.get("GROWI_URL", "http://localhost:3000").rstrip("/")
GROWI_TOKEN = os.environ["GROWI_TOKEN"]

# 読み取り元フォルダ
SOURCE_DIR = "coding-rules"

# GROWI上の作成先ルート
ROOT_GROWI_PATH = "/user/ikkei/コーディング規約3"


def markdown_file_to_growi_path(md_file: Path, source_root: Path) -> str:
    """
    MarkdownファイルのパスからGROWIのページパスを作る。

    例:
      coding-rules/index.md
        -> /usr/コーディング規約3

      coding-rules/naming/general.md
        -> /usr/コーディング規約3/naming/general
    """

    rel_path = md_file.relative_to(source_root)

    # 拡張子 .md を除去
    page_parts = list(rel_path.with_suffix("").parts)

    # index.md は親ページ扱いにする
    if page_parts[-1].lower() == "index":
        page_parts = page_parts[:-1]

    if page_parts:
        return ROOT_GROWI_PATH + "/" + "/".join(page_parts)
    else:
        return ROOT_GROWI_PATH


def create_or_update_page(path: str, body: str) -> None:
    url = f"{GROWI_URL}/_api/v3/page"

    payload = {
        "access_token": GROWI_TOKEN,
        "path": path,
        "body": body,
        # 必要なら公開範囲指定
        # "grant": 1,
    }

    res = requests.post(url, json=payload, timeout=30)

    if res.status_code >= 400:
        print(f"ERROR {path}: {res.status_code} {res.text}")
    else:
        print(f"OK {path}")


def main():
    base = Path(__file__).resolve().parent
    source_root = base / SOURCE_DIR

    md_files = sorted(source_root.rglob("*.md"))

    if not md_files:
        print(f"Markdownファイルが見つかりません: {source_root}")
        return

    for md_file in md_files:
        growi_path = markdown_file_to_growi_path(md_file, source_root)
        body = md_file.read_text(encoding="utf-8")

        print(f"{md_file.relative_to(base)} -> {growi_path}")
        create_or_update_page(growi_path, body)


if __name__ == "__main__":
    main()