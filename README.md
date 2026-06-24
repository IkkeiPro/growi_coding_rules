# GROWI 取り込み用ファイル
## 中身
- `coding-rules/index.md`
- `coding-rules/naming/general.md`
- `coding-rules/naming/class.md`
- `coding-rules/naming/method.md`
- `import_to_growi.py`

## 使い方
`import_to_growi.py` でGROWIにAPIで投稿する。
```bat
pip install requests
set GROWI_URL=http://localhost:3000
set GROWI_TOKEN=発行したトークン
python import_to_growi.py
```

