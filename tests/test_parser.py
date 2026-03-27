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
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from parsers.fields import parse_all

CACHE_DIR = Path("output/cache")


# ---------------------------------------------------------------------------
# 型定義
# ---------------------------------------------------------------------------
# 各エントリは (checker_func, description) のタプル。
# checker_func(v) は値 v（str）が期待型に合致すれば True を返す。
# None は全型でパスとする（欠損は型チェック対象外）。

def _is_int(v):
    return bool(re.fullmatch(r"\d+", str(v).strip()))

def _is_float(v):
    return bool(re.fullmatch(r"[\d,]+\.?\d*", str(v).replace(",", "").strip()))

def _is_pct(v):
    try:
        return 0.0 <= float(str(v).replace(",", "")) <= 100.0
    except ValueError:
        return False

def _is_year(v):
    return bool(re.fullmatch(r"\d{4}(\.\d+)?", str(v).strip()))

def _is_rating(v):
    return bool(re.fullmatch(r"[A-D]+[+\-]?|―|-", str(v).strip()))

def _is_score(v):
    s = str(v).strip()
    return s in ("―", "-") or bool(re.fullmatch(r"\d{1,3}\.\d", s))

def _is_nonempty(v):
    return len(str(v).strip()) > 0

# フィールド名 -> (checker, 型説明)
FIELD_TYPES: dict[str, tuple] = {
    # 基本情報
    "tel":              (_is_nonempty, "電話番号文字列"),
    "established":      (_is_year,    "年.月 (例: 1926.6)"),
    "listed":           (lambda v: _is_year(v) or str(v).strip() in ("―", "-"),
                                       "年.月 or ―"),
    "fiscal_end":       (_is_nonempty, "決算月文字列 (例: 3月)"),
    "address":          (_is_nonempty, "住所文字列"),
    "description":      (_is_nonempty, "特色テキスト"),

    # CSR評価レーティング
    "csr_hr_rating":    (_is_rating, "A-D系レーティング"),
    "csr_env_rating":   (_is_rating, "A-D系レーティング"),
    "csr_gov_rating":   (_is_rating, "A-D系レーティング"),
    "csr_soc_rating":   (_is_rating, "A-D系レーティング"),
    "csr_bsc_rating":   (_is_rating, "A-D系レーティング"),
    "fin_grwth_rating": (_is_rating, "A-D系レーティング"),
    "fin_prft_rating":  (_is_rating, "A-D系レーティング"),
    "fin_sfty_rating":  (_is_rating, "A-D系レーティング"),
    "fin_scl_rating":   (_is_rating, "A-D系レーティング"),

    # CSR評価スコア
    "csr_hr_score":     (_is_score, "数値 or ―"),
    "csr_env_score":    (_is_score, "数値 or ―"),
    "csr_gov_score":    (_is_score, "数値 or ―"),
    "csr_soc_score":    (_is_score, "数値 or ―"),
    "csr_bsc_score":    (_is_score, "数値 or ―"),
    "fin_grwth_score":  (_is_score, "数値 or ―"),
    "fin_prft_score":   (_is_score, "数値 or ―"),
    "fin_sfty_score":   (_is_score, "数値 or ―"),
    "fin_scl_score":    (_is_score, "数値 or ―"),

    # 株主情報
    "shares_total":     (_is_float, "数値（千株）"),
    "shareholders_n":   (_is_float, "数値（人）"),
    "major_share_pct":  (_is_pct,   "0〜100の数値（%）"),
    "float_pct":        (_is_pct,   "0〜100の数値（%）"),

    # 取締役・監査役
    "n_drctr":          (_is_int,  "整数"),
    "n_cap_drctr":      (_is_int,  "整数"),
    "n_wm_drctr":       (_is_int,  "整数"),
    "n_out_drctr":      (_is_int,  "整数"),
    "n_adtr":           (_is_int,  "整数"),
    "n_out_adtr":       (_is_int,  "整数"),

    # 環境負荷量
    "energy_gj":        (_is_float, "数値"),
    "water_m3":         (_is_float, "数値"),
    "ghg_tco2":         (_is_float, "数値"),
    "chemical_t":       (_is_float, "数値"),
    "waste_t":          (_is_float, "数値"),
    "wastewater_m3":    (_is_float, "数値"),
    "nox_t":            (_is_float, "数値"),
    "sox_t":            (_is_float, "数値"),
    "env_scp3":         (_is_float, "数値"),

    # 環境テーブル
    "iso14001_dom":     (_is_pct,  "0〜100の数値（%）"),
    "iso14001_ovs":     (_is_pct,  "0〜100の数値（%）"),
    "iso9000s_dom":     (_is_pct,  "0〜100の数値（%）"),
    "iso9000s_ovs":     (_is_pct,  "0〜100の数値（%）"),
    "env_cost":         (lambda v: _is_float(v) or str(v).strip() in ("―", "-"), "数値（百万円）or ―"),
    "bio_dvrsty_prjct": (_is_float, "数値（百万円）"),

    # 通報・法令違反件数
    "n_accstn":         (_is_int, "整数"),
    "dmstc_lw_case":    (_is_int, "整数"),
    "ovrsea_lw_violtn": (_is_int, "整数"),

    # 社会貢献・政治献金
    "scl_cntrbtn_amnt":  (_is_float, "数値（百万円）"),
    "pltcl_cntrbtn_amnt":(_is_float, "数値（百万円）"),

    # グリーン購入比率
    "spply_grn_buy":    (_is_pct, "0〜100の数値（%）"),
}


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


def run_all(type_only: bool = False):
    files = sorted(CACHE_DIR.glob("*.json"))
    print(f"テスト件数: {len(files)}\n")

    rows = []
    for f in files:
        data = json.load(open(f, encoding="utf-8"))
        result = parse_all(data["full_lines"])
        result["_file"] = f.stem
        rows.append(result)

    if not rows:
        print("キャッシュが空です。先に main.py --dir を実行してください。")
        return

    total = len(rows)

    # ---- 型チェック ----
    violations = check_types(rows)

    if not type_only:
        seen = dict.fromkeys(k for r in rows for k in r if not k.startswith("_"))
        all_keys = list(seen)

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

    # ---- 型違反サマリー ----
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
