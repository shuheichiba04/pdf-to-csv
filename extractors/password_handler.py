"""
PDFパスワード解除モジュール
- .env の PDF_PASSWORDS リストを順番に試行
- 解除済みの fitz.Document を返す
"""

import fitz  # PyMuPDF
from pathlib import Path


def open_pdf(pdf_path: str | Path, passwords: list[str] = None) -> dict:
    """
    PDFを開く。暗号化されている場合はパスワードリストを試行する。

    Returns:
        {
            "doc": fitz.Document or None,
            "password_used": "xxxx" or None,
            "password_failed": False,
            "error": None or "エラーメッセージ",
        }
    """
    result = {
        "doc": None,
        "password_used": None,
        "password_failed": False,
        "error": None,
    }

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        result["error"] = f"ファイルが見つかりません: {pdf_path}"
        return result

    try:
        doc = fitz.open(str(pdf_path))

        if not doc.is_encrypted:
            result["doc"] = doc
            return result

        # パスワードなし（空文字）を最初に試す
        candidates = [""] + (passwords or [])
        for pw in candidates:
            if doc.authenticate(pw):
                result["doc"] = doc
                result["password_used"] = pw if pw else None
                return result

        doc.close()
        result["password_failed"] = True
        result["error"] = "パスワード認証に失敗しました"

    except Exception as e:
        result["error"] = str(e)

    return result
