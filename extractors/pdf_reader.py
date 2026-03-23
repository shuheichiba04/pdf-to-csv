"""
PDF読み込みモジュール
- 全ページテキストをページ境界マーカー付きで返す
- get_text("words") を使った座標ベースの行再構築も提供
- パスワード処理は password_handler.py に委譲
"""

import fitz  # PyMuPDF
from pathlib import Path


def _words_to_lines(
    words: list,
    y_tolerance: float = 3.0,
    column_gap_threshold: float = 40.0,
) -> list[str]:
    """
    get_text("words") の出力をY座標でグループ化し、
    X座標順に単語を並べた行リストを返す。

    同一Y行内に column_gap_threshold (pt) 以上のX座標ギャップがある場合、
    そこをカラム境界とみなして左・右カラムを別々の行として出力する。
    これにより2カラムレイアウトの左右テキスト混入を防ぐ。

    Args:
        words: fitz の get_text("words") の出力
               各要素: (x0, y0, x1, y1, text, block_no, line_no, word_no)
        y_tolerance: 同じ行とみなすY座標の差の閾値（pt）
        column_gap_threshold: カラム境界とみなす単語間X座標ギャップの閾値（pt）
                              curr.x0 - prev.x1 がこの値以上でカラム分割する

    Returns:
        行文字列のリスト（Y座標昇順）。カラム分割した場合は左→右の順で別行になる。
    """
    if not words:
        return []

    # Y座標でソート後、近いY値を同じ行にまとめる
    sorted_words = sorted(words, key=lambda w: (w[1], w[0]))

    rows: list[list] = []
    current_row: list = [sorted_words[0]]
    current_y: float = sorted_words[0][1]

    for w in sorted_words[1:]:
        if abs(w[1] - current_y) <= y_tolerance:
            current_row.append(w)
        else:
            rows.append(current_row)
            current_row = [w]
            current_y = w[1]
    rows.append(current_row)

    # 各行内をX座標順に並べ、大きなギャップでカラム分割して出力
    lines = []
    for row in rows:
        row_sorted = sorted(row, key=lambda w: w[0])

        # 隣接単語間のギャップを検査してカラムグループに分割
        column_groups: list[list] = []
        current_group = [row_sorted[0]]
        for prev, curr in zip(row_sorted, row_sorted[1:]):
            if curr[0] - prev[2] >= column_gap_threshold:  # curr.x0 - prev.x1
                column_groups.append(current_group)
                current_group = [curr]
            else:
                current_group.append(curr)
        column_groups.append(current_group)

        # 各カラムグループを独立した行として追加（カラム分割なしなら1行）
        for group in column_groups:
            lines.append("\t".join(w[4] for w in group))

    return lines


def read_pdf(pdf_path: str | Path, doc: fitz.Document = None) -> dict:
    """
    PDFを開いてテキストを抽出する。
    既に開済みの fitz.Document を渡すこともできる（パスワード解除済みの場合など）。

    Returns:
        {
            "pages": [
                {
                    "page": 1,
                    "text": "...",        # get_text() のデフォルト出力
                    "lines": ["...", ...], # 座標ベースで行再構築したもの（タブ区切り）
                },
                ...
            ],
            "full_text": "...",   # デフォルトテキストの全ページ結合（=PAGE N= マーカー付き）
            "full_lines": "...",  # 座標ベース行の全ページ結合（=PAGE N= マーカー付き）
            "page_count": 10,
            "error": None or "エラーメッセージ",
        }
    """
    result = {
        "pages": [],
        "full_text": "",
        "full_lines": "",
        "page_count": 0,
        "error": None,
    }

    close_after = doc is None

    try:
        if doc is None:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                result["error"] = f"ファイルが見つかりません: {pdf_path}"
                return result
            doc = fitz.open(str(pdf_path))

        if doc.is_encrypted:
            result["error"] = "PDFが暗号化されています。password_handler で解除してから渡してください。"
            return result

        result["page_count"] = len(doc)

        pages = []
        full_text_parts = []
        full_lines_parts = []

        for i, page in enumerate(doc, start=1):
            text = page.get_text()
            words = page.get_text("words")
            # page1のみカラム分離（CSR/財務評価が左右2カラムレイアウト）
            # page2以降は環境データ等の表があり閾値なしで結合する
            gap_threshold = 40.0 if i == 1 else float("inf")
            lines = _words_to_lines(words, y_tolerance=3.0, column_gap_threshold=gap_threshold)

            pages.append({"page": i, "text": text, "lines": lines})
            full_text_parts.append(f"=== PAGE {i} ===\n{text}")
            full_lines_parts.append(f"=== PAGE {i} ===\n" + "\n".join(lines))

        result["pages"] = pages
        result["full_text"] = "\n".join(full_text_parts)
        result["full_lines"] = "\n".join(full_lines_parts)

    except Exception as e:
        result["error"] = str(e)
    finally:
        if close_after and doc:
            doc.close()

    return result
