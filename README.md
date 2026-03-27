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
│   ├── field_parser.py      # 正規表現によるフィールド抽出（parse_all）
│   ├── field_schema.py      # フィールドごとの期待型定義（FIELD_TYPES）
│   └── column_map.py        # CSV出力列順・日本語ラベル定義（COLUMNS）
├── tests/
│   └── test_parser.py       # キャッシュを使ったフィールド精度・型チェック
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
python -X utf8 tests/test_parser.py --type-only
python -X utf8 tests/test_parser.py --file "2019年版 （4045） 東亞合成（株）"
```

## 抽出フィールドと出力列名

CSV は1行目に日本語ラベル、2行目に英語変数名、3行目以降にデータを出力する。
列定義は `parsers/column_map.py` の `COLUMNS` で管理している。

| カテゴリ       | 英語変数名（例）                                                   |
| -------------- | ------------------------------------------------------------------ |
| 基本情報       | TEL, EstblshYr, LstngYr, AccntPrd, cmpAdrs, Chrctrstc             |
| CSR評価        | CSRHrRtng/Scr, CSREnvRtng/Scr, CSRGovRtng/Scr, CSRSocRtng/Scr, CSRBscRtng/Scr |
| 財務評価       | FinGrwthRtng/Scr, FinPrftRtng/Scr, FinSftyRtng/Scr, FinSclRtng/Scr |
| CSR基本・体制  | Prncpls, Mtralty, CSRDept, CSROffcr, ESGInfrmtn, SRIIndx, ...     |
| ガバナンス     | ShrhldrRght, Trnsprncy, Rspnsblty, ShrhldrDialg, ...              |
| 取締役・株主   | NofDrctr, NofAdtr, NofShare, NofShrhldr, SpcfStckRatio, ...       |
| 法令・内部統制 | LwCmplaDept, AccstnHelp, NofAccstn, DmstcLwCase, ISMS, BCP, ...   |
| 環境負荷量     | EnrgyGJ, WtrM3, GhgTco2, WasteT, EnvScp3, ...                     |
| 環境施策       | ISO14001Dom/Ovs, GrnBuy, ClimtEffrt, RnwablEnrgy, CO2Effrt, ...   |
| 社会貢献       | SclCntrbtnAmnt, PltclCntrbtnAmnt, JpnErthqkSpprt, ...             |

## 技術メモ

- 今回対象としたpdfデータに日本語情報が埋め込まれており、ある程度高い精度でデータを取得できそうであったためOCRではなくPyMuPDFを使用
- LLMによるデータ化はコストがかかるため、できる限り正規表現などで取得する方針
- 本リポジトリではpdfからのデータ抽出のみを対象とし、変数加工はStataで行う方針とする
- PDFの2カラムレイアウトに対応するため、PyMuPDFの座標情報（`get_text("words")`）を使ってY座標でグループ化・X座標でソートして行を再構築している
- 1ページ目（CSR/財務評価）はカラム間ギャップ40pt以上で左右カラムを分離、2ページ目以降（環境データ等）は分離なし
- 抽出テキストは `output/cache/` にJSONでキャッシュされ、バッチ開始時に自動クリアされる
