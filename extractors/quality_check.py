"""
テキスト品質チェックモジュール
- 文字化け・制御文字の混入率
- 日本語文字の出現比率
- 行あたり文字数の極端な偏り

返り値: "ok" / "warning" / "bad"
"""

import re
import unicodedata


def check_quality(text: str) -> dict:
    """
    テキストの品質を判定する。

    Returns:
        {
            "status": "ok" | "warning" | "bad",
            "reasons": [...],   # 問題があった場合の理由リスト
            "stats": {...},     # 各指標の数値
        }
    """
    if not text or len(text.strip()) == 0:
        return {"status": "bad", "reasons": ["テキストが空"], "stats": {}}

    reasons = []
    stats = {}

    total_chars = len(text)

    # --- 制御文字・文字化けの割合 ---
    # 印字不可能な制御文字（改行・タブ以外）
    control_chars = sum(
        1 for c in text
        if unicodedata.category(c) == "Cc" and c not in ("\n", "\t", "\r")
    )
    control_ratio = control_chars / total_chars
    stats["control_ratio"] = round(control_ratio, 4)
    if control_ratio > 0.05:
        reasons.append(f"制御文字が多い ({control_ratio:.1%})")

    # --- 日本語文字の比率 ---
    # ひらがな・カタカナ・漢字を日本語文字とみなす
    japanese_chars = sum(
        1 for c in text
        if "\u3040" <= c <= "\u9FFF" or "\uF900" <= c <= "\uFAFF"
    )
    japanese_ratio = japanese_chars / total_chars
    stats["japanese_ratio"] = round(japanese_ratio, 4)
    # 日本語PDFで日本語がほぼ0なら構造が崩れている可能性
    if japanese_ratio < 0.01:
        reasons.append(f"日本語文字が極端に少ない ({japanese_ratio:.1%})")

    # --- 行あたり文字数の分布 ---
    lines = [l for l in text.split("\n") if l.strip()]
    if lines:
        lengths = [len(l) for l in lines]
        avg_len = sum(lengths) / len(lengths)
        # 1文字以下の行が大多数なら構造が壊れている
        single_char_ratio = sum(1 for l in lengths if l <= 1) / len(lengths)
        stats["avg_line_length"] = round(avg_len, 1)
        stats["single_char_line_ratio"] = round(single_char_ratio, 4)
        if single_char_ratio > 0.5:
            reasons.append(f"1文字以下の行が多い ({single_char_ratio:.1%})")

    # --- 判定 ---
    if len(reasons) == 0:
        status = "ok"
    elif len(reasons) == 1 and control_ratio <= 0.1:
        status = "warning"
    else:
        status = "bad"

    return {"status": status, "reasons": reasons, "stats": stats}
