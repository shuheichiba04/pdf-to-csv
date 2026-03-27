"""
パーサー精度テスト。

output/cache/*.json を読んでフィールド抽出を実行し、
各フィールドの取得率・欠損率・サンプル値と型チェック結果を表示する。

型チェックは処理を止めず、期待型から外れた値の件数・サンプルを表示する。

使い方:
    python -X utf8 tests/test_parser.py
    python -X utf8 tests/test_parser.py --file "2017年版 （3405） （株）クラレ  "  # 1件詳細
    python -X utf8 tests/test_parser.py --type-only  # 型チェック結果のみ表示
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from parsers.field_parser import parse_all
from parsers.field_schema import FIELD_TYPES

CACHE_DIR = Path("output/cache")


def check_types(rows: list[dict]) -> dict[str, list]:
    """
    各フィールドの型チェックを実行する。
    戻り値: {field: [(file, value), ...]} — 型違反のあったファイルと値のリスト
    """
    violations: dict[str, list] = {}
    for field, (checker, _) in FIELD_TYPES.items():
        bad = []
        for row in rows:
            v = row.get(field)
            if v is None:
                continue  # 欠損はスキップ
            try:
                ok = checker(v)
            except Exception:
                ok = False
            if not ok:
                bad.append((row.get("_file", "?"), v))
        if bad:
            violations[field] = bad
    return violations


def load_rows() -> list[dict]:
    """キャッシュ全件を読み込んでパース済み行リストを返す。"""
    files = sorted(CACHE_DIR.glob("*.json"))
    print(f"テスト件数: {len(files)}\n")
    rows = []
    for f in files:
        data = json.load(open(f, encoding="utf-8"))
        result = parse_all(data["full_lines"])
        result["_file"] = f.stem
        rows.append(result)
    return rows


def print_coverage_table(rows: list[dict], violations: dict[str, list]):
    """フィールドごとの取得率・型NG件数・サンプル値を表形式で出力する。"""
    total = len(rows)
    all_keys = list(dict.fromkeys(k for r in rows for k in r if not k.startswith("_")))

    print(f"{'フィールド':<40} {'取得':>5} {'欠損':>5} {'取得率':>6}  {'型NG':>5}  サンプル値（最初の3件）")
    print("-" * 115)

    for key in all_keys:
        values = [r.get(key) for r in rows]
        got   = sum(1 for v in values if v is not None)
        miss  = total - got
        rate  = got / total * 100
        samples = [v for v in values if v is not None][:3]
        sample_str = " | ".join(str(s)[:20] for s in samples)
        type_ng = len(violations.get(key, []))
        ng_str = f"{type_ng:>5}" if type_ng else "     "
        print(f"{key:<40} {got:>5} {miss:>5} {rate:>5.0f}%  {ng_str}  {sample_str}")


def print_type_violations(violations: dict[str, list]):
    """型違反サマリーを出力する。"""
    print(f"\n{'='*60}")
    print(f"型チェック結果  違反フィールド数: {len(violations)} / {len(FIELD_TYPES)}")
    print(f"{'='*60}")
    if not violations:
        print("型違反なし")
        return

    for field, bad_list in violations.items():
        _, desc = FIELD_TYPES[field]
        print(f"\n【{field}】 期待型: {desc}  違反: {len(bad_list)}件")
        for fname, val in bad_list[:5]:
            print(f"  {fname[:35]:<35}  {repr(str(val)[:60])}")
        if len(bad_list) > 5:
            print(f"  ... 他 {len(bad_list)-5} 件")


def run_all(type_only: bool = False):
    rows = load_rows()
    if not rows:
        print("キャッシュが空です。先に main.py --dir を実行してください。")
        return

    violations = check_types(rows)

    if not type_only:
        print_coverage_table(rows, violations)

    print_type_violations(violations)


def run_single(stem: str):
    path = CACHE_DIR / (stem + ".json")
    if not path.exists():
        candidates = list(CACHE_DIR.glob(f"*{stem}*.json"))
        if not candidates:
            print(f"キャッシュが見つかりません: {stem}")
            return
        path = candidates[0]

    data = json.load(open(path, encoding="utf-8"))
    result = parse_all(data["full_lines"])
    result["_file"] = path.stem

    print(f"FILE: {path.stem}\n")
    for k, v in result.items():
        if k.startswith("_"):
            continue
        checker_desc = FIELD_TYPES.get(k)
        if checker_desc and v is not None:
            try:
                ok = checker_desc[0](v)
            except Exception:
                ok = False
            mark = "  " if ok else "✗型"
        else:
            mark = "  " if v is not None else "✗ "
        print(f"  {mark} {k:<40} {v}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="単体確認（キャッシュのstem名）")
    parser.add_argument("--type-only", action="store_true", help="型チェック結果のみ表示")
    args = parser.parse_args()

    if args.file:
        run_single(args.file)
    elif args.type_only:
        run_all(type_only=True)
    else:
        run_all(type_only=False)
