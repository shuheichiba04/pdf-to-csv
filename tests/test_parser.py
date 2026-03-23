"""
パーサー精度テスト。

output/cache/*.json を読んでフィールド抽出を実行し、
各フィールドの取得率・欠損率・サンプル値を表示する。

使い方:
    python -X utf8 tests/test_parser.py
    python -X utf8 tests/test_parser.py --file "2017年版 （3405） （株）クラレ  "  # 1件詳細
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from parsers.fields import parse_all

CACHE_DIR = Path("output/cache")


def run_all():
    files = sorted(CACHE_DIR.glob("*.json"))
    print(f"テスト件数: {len(files)}\n")

    # 全件パース
    rows = []
    for f in files:
        data = json.load(open(f, encoding="utf-8"))
        result = parse_all(data["full_lines"])
        result["_file"] = f.stem
        rows.append(result)

    if not rows:
        print("キャッシュが空です。先に main.py --dir を実行してください。")
        return

    # フィールドごとの取得率を集計
    # rows[0] 基準ではなく全rowsのキー和集合を使う（ファイルによってキーが異なる場合に対応）
    seen = dict.fromkeys(k for r in rows for k in r if not k.startswith("_"))
    all_keys = list(seen)
    total = len(rows)

    print(f"{'フィールド':<40} {'取得':>5} {'欠損':>5} {'取得率':>6}  サンプル値（最初の3件）")
    print("-" * 100)

    for key in all_keys:
        values = [r.get(key) for r in rows]
        got   = sum(1 for v in values if v is not None)
        miss  = total - got
        rate  = got / total * 100
        # Noneでないサンプルを最大3件
        samples = [v for v in values if v is not None][:3]
        sample_str = " | ".join(str(s)[:20] for s in samples)
        print(f"{key:<40} {got:>5} {miss:>5} {rate:>5.0f}%  {sample_str}")


def run_single(stem: str):
    path = CACHE_DIR / (stem + ".json")
    if not path.exists():
        # 部分一致で探す
        candidates = list(CACHE_DIR.glob(f"*{stem}*.json"))
        if not candidates:
            print(f"キャッシュが見つかりません: {stem}")
            return
        path = candidates[0]

    data = json.load(open(path, encoding="utf-8"))
    result = parse_all(data["full_lines"])

    print(f"FILE: {path.stem}\n")
    for k, v in result.items():
        mark = "  " if v is not None else "✗ "
        print(f"  {mark}{k:<40} {v}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="単体確認（キャッシュのstem名）")
    args = parser.parse_args()

    if args.file:
        run_single(args.file)
    else:
        run_all()
