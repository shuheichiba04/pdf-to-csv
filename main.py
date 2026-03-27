"""
PDFからテキストを抽出してCSV化するパイプライン。

使い方:
    python main.py --file path/to/file.pdf
    python main.py --dir  path/to/pdfs/

キャッシュ:
    --dir 実行時に output/cache/ へファイル単位でJSONを保存する。
    バッチ開始時にキャッシュをクリアするので、前回の残骸は残らない。
    --file 実行時はキャッシュを使わない（デバッグ向け単体実行のため）。
"""

import argparse   # --file / --dir コマンドライン引数の解析
import json        # キャッシュ（output/cache/*.json）の読み書き
import os          # PDF_PASSWORDS 等の環境変数取得（os.getenv）
import shutil      # キャッシュディレクトリの一括削除（shutil.rmtree）
import sys         # Windows コンソールの UTF-8 設定（sys.stdout.reconfigure）
from pathlib import Path  # ファイルパス操作（PDF走査・キャッシュパス生成）

import pandas as pd  # rows リストを DataFrame 化して CSV 出力

# Windows コンソールの文字化け対策
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv  # .env から PDF_PASSWORDS 等の設定を環境変数に読み込む

from extractors.password_handler import open_pdf       # パスワード試行・PDF オープン
from extractors.pdf_reader import read_pdf             # PyMuPDF でテキスト抽出（full_text / full_lines）
from extractors.quality_check import check_quality     # テキスト品質チェック（ok/warning/bad）
from parsers.field_parser import parse_all                   # 正規表現で全フィールドを抽出して dict を返す
from parsers.column_map import apply_column_map        # 出力カラム順・名称マッピング

load_dotenv()

CACHE_DIR = Path("output/cache")


def get_passwords() -> list[str]:
    raw = os.getenv("PDF_PASSWORDS", "")
    return [p.strip() for p in raw.split(",") if p.strip()]


def clear_cache():
    """キャッシュディレクトリを削除して再作成する。"""
    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)
    CACHE_DIR.mkdir(parents=True)


def save_cache(pdf_path: Path, extracted: dict):
    """
    extracted（full_text / full_lines / pages）をJSONで保存する。
    ファイル名は元のPDF名と同じ（拡張子を .json に変える）。
    """
    cache_path = CACHE_DIR / (pdf_path.stem + ".json")
    # pages内の lines は list[str] なのでそのままシリアライズ可能
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(extracted, f, ensure_ascii=False, indent=2)


def process_pdf(pdf_path: Path, passwords: list[str], use_cache: bool = False) -> dict:
    """1つのPDFを処理してフィールド辞書を返す。"""

    row = {
        "File":           pdf_path.name,
        "PageCount":      None,
        "password_used":  None,
        "password_failed": False,
        "TextQuality":    None,
        "quality_reasons": None,
        "Error":          None,
    }

    # パスワード解除 & オープン
    opened = open_pdf(pdf_path, passwords)
    row["password_used"] = opened["password_used"]
    row["password_failed"] = opened["password_failed"]

    if opened["error"]:
        row["Error"] = opened["error"]
        row["TextQuality"] = "bad"
        return row

    # テキスト抽出
    extracted = read_pdf(pdf_path, doc=opened["doc"])

    # doc を明示的に閉じる（open_pdf が開いたままにしているため）
    if opened["doc"]:
        opened["doc"].close()

    row["PageCount"] = extracted["page_count"]

    if extracted["error"]:
        row["Error"] = extracted["error"]
        row["TextQuality"] = "bad"
        return row

    # キャッシュに保存
    if use_cache:
        save_cache(pdf_path, extracted)

    # テキスト品質チェック
    quality = check_quality(extracted["full_text"])
    row["TextQuality"] = quality["status"]
    row["quality_reasons"] = "; ".join(quality["reasons"]) if quality["reasons"] else ""

    # フィールド抽出
    row.update(parse_all(extracted["full_lines"]))

    return row


def run_batch(input_dir: Path, passwords: list[str], csv_path: Path):
    pdf_files = sorted(input_dir.glob("**/*.pdf"))
    print(f"{len(pdf_files)} 件のPDFを処理します")

    print(f"キャッシュをクリア: {CACHE_DIR}")
    clear_cache()

    rows = []
    for pdf_path in pdf_files:
        print(f"  処理中: {pdf_path.name}")
        try:
            row = process_pdf(pdf_path, passwords, use_cache=True)
        except Exception as e:
            print(f"    予期しないエラー: {e}")
            continue
        rows.append(row)
        print(f"    品質: {row['TextQuality']}  ページ数: {row['PageCount']}")
        if row.get("quality_reasons"):
            print(f"    理由: {row['quality_reasons']}")
        if row.get("Error"):
            print(f"    エラー: {row['Error']}")

    csv_path.parent.mkdir(parents=True, exist_ok=True)

    jp_labels, en_names, data_rows = apply_column_map(rows)
    # pandasのcolumn行=英語変数名（2行目）、その上に日本語ラベル行（1行目）を手書き
    import csv, io
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(jp_labels)   # 1行目: 日本語ラベル
    writer.writerow(en_names)    # 2行目: 英語変数名
    for r in data_rows:
        writer.writerow([("" if v is None else v) for v in r])
    csv_path.write_bytes(("\ufeff" + buf.getvalue()).encode("utf-8"))
    print(f"\nCSV出力: {csv_path}  ({len(rows)} 行 + ヘッダ2行)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=Path, help="単体PDFのパス（キャッシュなし）")
    parser.add_argument("--dir", type=Path, help="PDFディレクトリのパス（キャッシュあり）")
    args = parser.parse_args()

    passwords = get_passwords()
    csv_path = Path(os.getenv("CSV_OUTPUT_PATH", "output/result.csv"))

    if args.file:
        row = process_pdf(args.file, passwords, use_cache=False)
        for k, v in row.items():
            print(f"  {k}: {v}")
    elif args.dir:
        run_batch(args.dir, passwords, csv_path)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
