"""
フィールドスキーマ定義。

各フィールドの期待型チェック関数と説明を一元管理する。
FIELD_TYPES は tests/test_parser.py と将来的な検証コードが参照する。

checker_func(v) は値 v（str）が期待型に合致すれば True を返す。
None は全型でパスとする（欠損は型チェック対象外）。
"""

import re


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


# 英語変数名 -> (checker, 型説明)
FIELD_TYPES: dict[str, tuple] = {
    # 基本情報
    "TEL":          (_is_nonempty, "電話番号文字列"),
    "EstblshYr":    (_is_year,    "年.月 (例: 1926.6)"),
    "LstngYr":      (lambda v: _is_year(v) or str(v).strip() in ("―", "-"),
                                   "年.月 or ―"),
    "AccntPrd":     (_is_nonempty, "決算月文字列 (例: 3月)"),
    "cmpAdrs":      (_is_nonempty, "住所文字列"),
    "Chrctrstc":    (_is_nonempty, "特色テキスト"),

    # CSR評価レーティング
    "CSRHrRtng":    (_is_rating, "A-D系レーティング"),
    "CSREnvRtng":   (_is_rating, "A-D系レーティング"),
    "CSRGovRtng":   (_is_rating, "A-D系レーティング"),
    "CSRSocRtng":   (_is_rating, "A-D系レーティング"),
    "CSRBscRtng":   (_is_rating, "A-D系レーティング"),
    "FinGrwthRtng": (_is_rating, "A-D系レーティング"),
    "FinPrftRtng":  (_is_rating, "A-D系レーティング"),
    "FinSftyRtng":  (_is_rating, "A-D系レーティング"),
    "FinSclRtng":   (_is_rating, "A-D系レーティング"),

    # CSR評価スコア
    "CSRHrScr":     (_is_score, "数値 or ―"),
    "CSREnvScr":    (_is_score, "数値 or ―"),
    "CSRGovScr":    (_is_score, "数値 or ―"),
    "CSRSocScr":    (_is_score, "数値 or ―"),
    "CSRBscScr":    (_is_score, "数値 or ―"),
    "FinGrwthScr":  (_is_score, "数値 or ―"),
    "FinPrftScr":   (_is_score, "数値 or ―"),
    "FinSftyScr":   (_is_score, "数値 or ―"),
    "FinSclScr":    (_is_score, "数値 or ―"),

    # 株主情報
    "NofShare":      (_is_float, "数値（千株）"),
    "NofShrhldr":    (_is_float, "数値（人）"),
    "SpcfStckRatio": (_is_pct,   "0〜100の数値（%）"),
    "FlotStckRatio": (_is_pct,   "0〜100の数値（%）"),

    # 取締役・監査役
    "NofDrctr":     (_is_int,  "整数"),
    "NofCapDrctr":  (_is_int,  "整数"),
    "NofWmDrctr":   (_is_int,  "整数"),
    "NofOutDrctr":  (_is_int,  "整数"),
    "NofAdtr":      (_is_int,  "整数"),
    "NofOutAdtr":   (_is_int,  "整数"),

    # 環境負荷量
    "EnrgyGJ":      (_is_float, "数値"),
    "WtrM3":        (_is_float, "数値"),
    "GhgTco2":      (_is_float, "数値"),
    "ChemT":        (_is_float, "数値"),
    "WasteT":       (_is_float, "数値"),
    "WstwtrM3":     (_is_float, "数値"),
    "NoxT":         (_is_float, "数値"),
    "SoxT":         (_is_float, "数値"),
    "EnvScp3":      (_is_float, "数値"),

    # 環境テーブル
    "ISO14001Dom":  (_is_pct,  "0〜100の数値（%）"),
    "ISO14001Ovs":  (_is_pct,  "0〜100の数値（%）"),
    "ISO9000SDom":  (_is_pct,  "0〜100の数値（%）"),
    "ISO9000SOvs":  (_is_pct,  "0〜100の数値（%）"),
    "EnvCost":      (lambda v: _is_float(v) or str(v).strip() in ("―", "-"), "数値（百万円）or ―"),
    "BioDvrstyPrjct": (_is_float, "数値（百万円）"),

    # 通報・法令違反件数
    "NofAccstn":    (_is_int, "整数"),
    "DmstcLwCase":  (_is_int, "整数"),
    "OvrseaLwVioltn": (_is_int, "整数"),

    # 社会貢献・政治献金
    "SclCntrbtnAmnt":  (_is_float, "数値（百万円）"),
    "PltclCntrbtnAmnt":(_is_float, "数値（百万円）"),

    # グリーン購入比率
    "SpplyGrnBuy":  (_is_pct, "0〜100の数値（%）"),
}
