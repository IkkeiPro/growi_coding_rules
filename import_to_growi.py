#!/usr/bin/env python3
"""
MarkdownファイルをGROWIに同期するスクリプトです。

処理内容:
  - coding-rules 配下の .md ファイルを再帰的に読み取る
  - GROWI上の /user/ikkei/コーディング規約3 配下に対応するページを作る
  - GROWI側とローカル側の本文を比較する
  - 差分がない場合は更新しない
  - ページがない場合は作成する
  - ページがあるが本文が違う場合は更新する

cmdでの実行例:
  set GROWI_URL=http://localhost:3000
  set GROWI_TOKEN=発行したAPIトークン
  py import_to_growi.py

差分確認だけしたい場合:
  set "DRY_RUN=1"
  py import_to_growi.py

実際に更新する場合:
  set "DRY_RUN=0"
  py import_to_growi.py
"""

import os
from pathlib import Path
import requests

GROWI_URL = os.environ.get("GROWI_URL", "http://localhost:3000").rstrip("/")
GROWI_TOKEN = os.environ["GROWI_TOKEN"]

# 1 にすると、更新対象を表示するだけでPOSTしない
DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"

# 読み取り元フォルダ
SOURCE_DIR = "coding-rules"

# GROWI上の作成先ルート
ROOT_GROWI_PATH = "/user/ikkei/コーディング規約3"


def markdown_file_to_growi_path(md_file: Path, source_root: Path) -> str:
    """
    MarkdownファイルのパスからGROWIのページパスを作る。

    例:
      coding-rules/index.md
        -> /user/ikkei/コーディング規約3

      coding-rules/naming/general.md
        -> /user/ikkei/コーディング規約3/naming/general
    """

    rel_path = md_file.relative_to(source_root)

    # 拡張子 .md を除去
    page_parts = list(rel_path.with_suffix("").parts)

    # index.md は親ページ扱いにする
    if page_parts and page_parts[-1].lower() == "index":
        page_parts = page_parts[:-1]

    if page_parts:
        return ROOT_GROWI_PATH + "/" + "/".join(page_parts)

    return ROOT_GROWI_PATH


def normalize_body(body: str | None) -> str:
    """
    差分比較用に本文を正規化する。
    WindowsのCRLFとGROWI側のLF差分で毎回更新されるのを防ぐ。
    """
    if body is None:
        return ""

    return body.replace("\r\n", "\n").replace("\r", "\n").strip()


def get_growi_page(path: str) -> dict | None:
    """
    GROWI上のページ情報を取得する。
    ページが存在しない場合は None を返す。
    """

    url = f"{GROWI_URL}/_api/v3/page"

    params = {
        "access_token": GROWI_TOKEN,
        "path": path,
    }

    res = requests.get(url, params=params, timeout=30)

    if res.status_code == 404:
        return None

    if res.status_code >= 400:
        print(f"ERROR GET {path}: {res.status_code} {res.text}")
        return None

    data = res.json()

    # GROWIのバージョン差分を考慮
    page = data.get("page") or data.get("data", {}).get("page")

    if not page:
        return None

    return page


def get_page_body(page: dict) -> str | None:
    """
    GROWIのページ情報から本文を取り出す。
    GROWIのバージョン差分を考慮して複数パターンを見る。
    """

    if page.get("body") is not None:
        return page["body"]

    revision = page.get("revision")
    if revision and revision.get("body") is not None:
        return revision["body"]

    return None


def create_page(path: str, body: str) -> bool:
    """
    GROWIにページを新規作成する。
    """

    url = f"{GROWI_URL}/_api/v3/page"

    payload = {
        "access_token": GROWI_TOKEN,
        "path": path,
        "body": body,
        # 必要なら公開範囲指定
        # "grant": 1,
    }

    if DRY_RUN:
        print(f"DRY_RUN CREATE {path}")
        return True

    res = requests.post(url, json=payload, timeout=30)

    if res.status_code >= 400:
        print(f"ERROR CREATE {path}: {res.status_code} {res.text}")
        return False

    print(f"CREATED {path}")
    return True

def update_page(page: dict, path: str, body: str) -> bool:
    """
    GROWIの既存ページを更新する。
    あなたの環境では /_api/pages.update が存在しないため、
    REST API v3 の /_api/v3/page に PUT する。
    """

    url = f"{GROWI_URL}/_api/v3/page"

    revision = page.get("revision") or {}

    page_id = page.get("_id")
    revision_id = revision.get("_id")

    if not page_id:
        print(f"ERROR UPDATE {path}: page _id が取得できません")
        print(f"page={page}")
        return False

    if not revision_id:
        print(f"ERROR UPDATE {path}: revision _id が取得できません")
        print(f"page={page}")
        return False

    payload = {
        "access_token": GROWI_TOKEN,
        "pageId": page_id,
        "revisionId": revision_id,
        "path": path,
        "body": body,
    }

    if DRY_RUN:
        print(f"DRY_RUN UPDATE {path}")
        return True

    res = requests.put(url, json=payload, timeout=30)

    if res.status_code >= 400:
        print(f"ERROR UPDATE {path}: {res.status_code} {res.text}")
        return False

    print(f"UPDATED {path}")
    return True


def sync_page(path: str, local_body: str) -> None:
    """
    ローカル本文とGROWI本文を比較し、差分がある場合だけ同期する。
    """

    page = get_growi_page(path)

    if page is None:
        print(f"CREATE {path}")
        create_page(path, local_body)
        return

    growi_body = get_page_body(page)

    if normalize_body(local_body) == normalize_body(growi_body):
        print(f"SKIP {path}")
        return

    print(f"CHANGE {path}")
    update_page(page, path, local_body)


def main() -> None:
    base = Path(__file__).resolve().parent
    source_root = base / SOURCE_DIR

    md_files = sorted(source_root.rglob("*.md"))

    if not md_files:
        print(f"Markdownファイルが見つかりません: {source_root}")
        return

    print(f"GROWI_URL: {GROWI_URL}")
    print(f"SOURCE_DIR: {source_root}")
    print(f"ROOT_GROWI_PATH: {ROOT_GROWI_PATH}")
    print(f"DRY_RUN: {DRY_RUN}")
    print("")

    for md_file in md_files:
        growi_path = markdown_file_to_growi_path(md_file, source_root)
        body = md_file.read_text(encoding="utf-8")

        print(f"{md_file.relative_to(base)} -> {growi_path}")
        sync_page(growi_path, body)


if __name__ == "__main__":
    main()