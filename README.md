# pdf-to-csv

日本語PDFからテキストを抽出し、構造化フィールドをCSVに変換するパイプライン。
2カラムレイアウトのPDFや、パスワード保護されたPDFに対応している。

## 構成

```
pdf-to-csv/
├── extractors/
│   ├── password_handler.py  # パスワード解除・PDFオープン
│   ├── pdf_reader.py        # PyMuPDF によるテキスト抽出（座標ベース行再構築）
│   └── quality_check.py     # テキスト品質チェック（文字化け検出）
├── parsers/
│   └── fields.py            # 正規表現によるフィールド抽出
├── tests/
│   └── test_parser.py       # キャッシュを使ったフィールド精度測定
├── main.py                  # エントリーポイント
├── requirements.txt
└── .env                     # パスワード・パス設定（要作成）
```

## セットアップ

```bash
pip install -r requirements.txt
```

`.env` を作成する：

```
PDF_PASSWORDS=password1,password2
PDF_INPUT_DIR=input/
CSV_OUTPUT_PATH=output/result.csv
```

## 使い方

**バッチ処理**（`input/` 以下の全PDFを処理してCSV出力）：

```bash
python -X utf8 main.py --dir input/
```

**単体ファイル確認**（キャッシュなし、結果を標準出力に表示）：

```bash
python -X utf8 main.py --file input/sample.pdf
```

**精度確認**（バッチ処理後、キャッシュから全フィールドの取得率を集計）：

```bash
python -X utf8 tests/test_parser.py
python -X utf8 tests/test_parser.py --file "2019年版 （4045） 東亞合成（株）"
```

## 抽出フィールド

| カテゴリ   | フィールド例                                               |
| ---------- | ---------------------------------------------------------- |
| 基本情報   | tel, established, listed, fiscal_end, address, description |
| CSR評価    | csr_hr_rating/score, csr_env_rating/score, csr_gov_rating/score, csr_soc_rating/score, csr_bsc_rating/score |
| 財務評価   | fin_grwth_rating/score, fin_prft_rating/score, fin_sfty_rating/score, fin_scl_rating/score |
| フラグ     | has_philosophy, has_materiality, esg_disclosure, sdgs, ... |
| CSR体制    | csr_dept_tenure, csr_dept_name, csr_officer_name, ...      |
| 株主情報   | shares_total, shareholders_n, major_share_pct, float_pct   |
| 環境負荷量 | energy_gj, water_m3, ghg_tco2, waste_t, ...                |
| SRI        | sri_index                                                  |

## 技術メモ

- 今回対象としたpdfデータに日本語情報が埋め込まれており、ある程度高い精度でデータを取得できそうであったためOCRではなくPyMuPDFを使用
- LLMによるデータ化はコストがかかるため、できる限り正規表現などで取得する方針
- 本リポジトリではpdfからのデータ抽出のみを対象とし、変数加工はStataで行う方針とする
- PDFの2カラムレイアウトに対応するため、PyMuPDFの座標情報（`get_text("words")`）を使ってY座標でグループ化・X座標でソートして行を再構築している
- 1ページ目（CSR/財務評価）はカラム間ギャップ40pt以上で左右カラムを分離、2ページ目以降（環境データ等）は分離なし
- 抽出テキストは `output/cache/` にJSONでキャッシュされ、バッチ開始時に自動クリアされる
