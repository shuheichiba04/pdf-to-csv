"""
フィールド抽出モジュール。

full_lines（座標ベース行テキスト）から各フィールドを取り出す。
マッチしなかった場合は None を返す（欠損は欠損として扱う）。

関数ごとに1フィールド（または関連フィールドのグループ）を担当する。
"""

import re


# ---------------------------------------------------------------------------
# ユーティリティ
# ---------------------------------------------------------------------------

def _first(pattern: str, text: str, group: int = 1):
    """text から pattern の最初のマッチを返す。なければ None。"""
    m = re.search(pattern, text)
    return m.group(group).strip() if m else None


def _tab_split(line: str) -> list[str]:
    """タブ区切り行を分割し、空要素を除去して返す。"""
    return [p.strip() for p in line.split("\t") if p.strip()]


# ---------------------------------------------------------------------------
# 基本情報（【キー】値 形式）
# ---------------------------------------------------------------------------

def parse_basic(lines: list[str]) -> dict:
    """
    TEL・設立・上場・決算期・本社住所・特色を抽出する。
    これらは 【キー】値 の安定した形式。
    """
    text = "\n".join(lines)
    return {
        "tel":        _first(r"【TEL】([\d\-－–()（）]+)", text),
        "established": _first(r"【設立】(\d[\d.]+)", text),
        "listed":     _first(r"【上場】([\d.]+|―|-)", text),
        "fiscal_end": _first(r"【決算期】(\S+)", text),
        # 長いキー名を先に試す（「本社」が「東京本社」より先にマッチするのを防ぐ）
        "address":    _first(r"【(?:東京本社|大阪本社|本店|本社)】([^\t\n]+)", text),
        "description": _first(r"【特色】([^\t\n]+)", text),
    }


# ---------------------------------------------------------------------------
# CSR評価・財務評価スコア（ラベル行・レーティング行・スコア行の3行セット）
# ---------------------------------------------------------------------------

# CSR評価・財務評価で出現する固定ラベルセット（右カラム混入テキストの除外に使う）
_CSR_LABELS  = {"人材活用", "環境", "企業統治", "社会性", "基本"}
_FIN_LABELS  = {"成長性", "収益性", "安全性", "規模"}

# ラベル日本語 → 列名用英字キーの変換マップ（英語略称、母音省略）
_LABEL_KEY = {
    "人材活用": "hr",
    "環境":     "env",
    "企業統治": "gov",
    "社会性":   "soc",
    "基本":     "bsc",
    "成長性":   "grwth",
    "収益性":   "prft",
    "安全性":   "sfty",
    "規模":     "scl",
}


def _parse_rating_block(lines: list[str], header: str) -> dict | None:
    """
    「人材活用\t環境\t...」のラベル行を探し、
    直後のレーティング行・スコア行を対応付けて返す。

    header: "CSR評価" or "財務評価"

    右カラムのテキストがタブで混入するため、ラベル行・レーティング行・スコア行は
    既知ラベル数（最大5）だけを取り、それ以降の要素は無視する。
    """
    valid_labels = _CSR_LABELS if header == "CSR評価" else _FIN_LABELS

    # ヘッダ行のインデックスを探す
    header_idx = None
    for i, l in enumerate(lines):
        if header in l:
            header_idx = i
            break
    if header_idx is None:
        return None

    # ヘッダの次の行からラベル・レーティング・スコアを探す
    # ラベル行を見つけたら、そこからさらに最大6行以内でrating/scoreを探す
    label_line = rating_line = score_line = None
    label_idx = None
    for i, l in enumerate(lines[header_idx + 1: header_idx + 8]):
        parts = _tab_split(l)
        if not parts:
            continue
        # ラベル行: 先頭要素が既知ラベルに含まれる（「人材活用」or「成長性」）
        if parts[0] in valid_labels:
            label_line = [p for p in parts if p in valid_labels]
            label_idx = header_idx + 1 + i
            break  # ラベル行が見つかったら即座にループを抜ける

    if label_line is None:
        return None

    # ラベル行の直後6行以内でrating行とscore行を探す
    for l in lines[label_idx + 1: label_idx + 7]:
        parts = _tab_split(l)
        if not parts:
            continue
        trimmed = parts[:len(label_line)]
        # レーティング行: 全要素が ―/- or A-D系 かつ、A-D文字を少なくとも1つ含む
        # （―だけの行はスコア行と区別できないため、rating行とみなさない）
        is_rating_val = lambda v: bool(re.match(r"^[A-D]+[+\-]?$|^―$|^-$", v))
        has_letter    = any(re.match(r"^[A-D]", v) for v in trimmed)
        if rating_line is None and all(is_rating_val(v) for v in trimmed) and has_letter:
            rating_line = trimmed
        # スコア行: 全要素が数値 or ―
        elif score_line is None and all(re.match(r"^\d+\.\d+$|^―$|^-$", v) for v in trimmed):
            score_line = trimmed
        # rating/score両方揃ったら終了
        if rating_line is not None and score_line is not None:
            break

    result = {}
    prefix = "csr" if header == "CSR評価" else "fin"
    for i, label in enumerate(label_line):
        key = _LABEL_KEY.get(label, label)
        result[f"{prefix}_{key}_rating"] = rating_line[i] if rating_line and i < len(rating_line) else None
        result[f"{prefix}_{key}_score"]  = score_line[i]  if score_line  and i < len(score_line)  else None

    return result


def parse_csr_ratings(lines: list[str]) -> dict:
    result = _parse_rating_block(lines, "CSR評価") or {}
    result.update(_parse_rating_block(lines, "財務評価") or {})
    return result


# ---------------------------------------------------------------------------
# 有無フラグ系（【キー】有/無/― などの単純フィールド）
# ---------------------------------------------------------------------------

# 取得対象のキーと出力列名のマッピング
# 値はタブ・行末・【 のいずれかで打ち切る（右カラム混入を防ぐ）
_FLAG_FIELDS = {
    "経営理念":                          "has_philosophy",
    "活動のマテリアリティ設定":            "has_materiality",
    "ステークホルダー・エンゲージメント":   "stakeholder_engagement",
    "活動の報告":                        "activity_report",
    "第三者の関与":                      "has_third_party",
    "英文の報告書":                      "has_eng_report",
    "統合報告書":                        "has_integrated_report",
    "ESG情報の開示":                     "esg_disclosure",
    "機関投資家・ESG調査機関等との対話":   "esg_investor_dialog",
    "ISO26000":                         "iso26000",
    "汚職・贈収賄防止":                   "anti_corruption_policy",
    "CSR調達の実施":                     "csr_procurement",
    "NPO・NGO連携":                     "npo_ngo",
    "SDGs":                             "sdgs",
    "内部監査部門":                      "internal_audit",
    "BCM構築":                          "bcm",
    "BCP策定":                          "bcp",
    "環境会計":                          "env_accounting",
    "EMS構築":                          "ems",
}

def parse_flags(lines: list[str]) -> dict:
    """
    【キー】有/無/―/開示/活用/... 形式のフィールドを一括取得。
    値はそのまま文字列で保持する（有無の正規化はCSV後処理で行う）。
    タブ区切りで右カラムのテキストが混入するため、タブ前までを取得する。
    """
    text = "\n".join(lines)
    result = {}
    for key, col in _FLAG_FIELDS.items():
        # 【キー】の直後〜タブか行末か次の【 まで
        val = _first(rf"【{re.escape(key)}】([^\t\n【]+)", text)
        result[col] = val

    # 「方針の文書化・公開」と「方針の文書化」の2種類が混在するため、長いキーを優先
    result["csr_policy_doc"] = (
        _first(r"【方針の文書化・公開】([^\t\n【]+)", text)
        or _first(r"【方針の文書化】([^\t\n【]+)", text)
    )

    return result


# ---------------------------------------------------------------------------
# CSR体制（部署・担当役員・業務比率）
# ---------------------------------------------------------------------------

def parse_csr_structure(lines: list[str]) -> dict:
    """
    CSR部署・担当役員・CSR業務比率を抽出する。

    【CSR部署】（専任）部署名  または  （兼任）部署名  または  無
    【CSR担当役員】専任有（役員名）  または  兼任有（役員名）  または  無
    【同・CSR業務比率】半分以下  など
    """
    text = "\n".join(lines)

    # CSR部署: （専任）or（兼任）を tenure、残りを部署名として分割
    csr_dept_tenure = None
    csr_dept_name = None
    m = re.search(r"【CSR部署】（(専任|兼任)）([^\t\n【]+)", text)
    if m:
        csr_dept_tenure = m.group(1)
        csr_dept_name = m.group(2).strip()
    else:
        # 無 or その他の値
        csr_dept_tenure = _first(r"【CSR部署】([^\t\n【]+)", text)

    # CSR担当役員: 専任有/兼任有 + （役員名）を分割
    csr_officer_tenure = None
    csr_officer_name = None
    m = re.search(r"【CSR担当役員】(専任有|兼任有)（([^）]+)）", text)
    if m:
        csr_officer_tenure = m.group(1)
        csr_officer_name = m.group(2).strip()
    else:
        csr_officer_tenure = _first(r"【CSR担当役員】([^\t\n【]+)", text)

    # 同・CSR業務比率
    csr_ratio = _first(r"【同・CSR業務比率】([^\t\n【]+)", text)

    return {
        "csr_dept_tenure": csr_dept_tenure,
        "csr_dept_name":   csr_dept_name,
        "csr_officer_tenure": csr_officer_tenure,
        "csr_officer_name":   csr_officer_name,
        "csr_ratio":       csr_ratio,
    }


# ---------------------------------------------------------------------------
# SRIインデックス等への組み入れ
# ---------------------------------------------------------------------------

def parse_sri(lines: list[str]) -> dict:
    """
    【SRIインデックス等への組み入れ】の値をタブ前まで取得する。
    複数インデックスが「、」区切りで並ぶが、タブで右カラムが混入するため
    タブ前までをそのまま文字列として保持する（後処理で分割可）。
    """
    text = "\n".join(lines)
    return {
        "sri_index": _first(r"【SRIインデックス等への組み入れ】([^\t\n【]+)", text),
    }


# ---------------------------------------------------------------------------
# 株主情報
# ---------------------------------------------------------------------------

def parse_shareholders(lines: list[str]) -> dict:
    text = "\n".join(lines)
    return {
        "shares_total":    _first(r"【株式数】([\d,]+)千株", text),
        "shareholders_n":  _first(r"【株主総数】([\d,]+)人", text),
        "major_share_pct": _first(r"【特定株比率】([\d.]+)%", text),
        "float_pct":       _first(r"【浮動株比率】([\d.]+)%", text),
    }


# ---------------------------------------------------------------------------
# 環境負荷量（固定指標を個別に取得）
# ---------------------------------------------------------------------------
# 行形式: 指標名（単位）\t最新年度値\t前年度値
# 直近年度（最後の列）を取得する。欠損は None。

_ENV_METRICS = {
    "総エネルギー投入量":      "energy_gj",
    "水資源投入量":            "water_m3",
    "温室効果ガス排出量":      "ghg_tco2",
    "特定化学物質排出量":      "chemical_t",
    "廃棄物等総排出量":        "waste_t",
    "総排水量":               "wastewater_m3",
    "NOX":                   "nox_t",
    "SOX":                   "sox_t",
}

def parse_env_data(lines: list[str]) -> dict:
    """
    環境負荷量の各指標について直近年度値（タブ区切り最初の数値）を取得する。

    2パターンに対応:
    A) 同一行: 「指標名（単位）\t数値\t数値」→ タブ直後の最初の数値を取る
    B) 別行  : 「指標名（単位）」の次行が「数値\t数値」→ 次行の最初の数値を取る
    """
    result = {col: None for col in _ENV_METRICS.values()}

    for metric, col in _ENV_METRICS.items():
        for i, line in enumerate(lines):
            if metric not in line:
                continue
            # パターンA: 同一行にタブ+数値がある
            m = re.search(rf"{re.escape(metric)}[^\t\n]*\t([\d,]+(?:\.\d+)?)", line)
            if m:
                result[col] = m.group(1)
                break
            # パターンB: 指標名のみの行 → 次行の先頭数値を取る
            if i + 1 < len(lines):
                m = re.match(r"([\d,]+(?:\.\d+)?)", lines[i + 1].strip())
                if m:
                    result[col] = m.group(1)
            break

    return result


# ---------------------------------------------------------------------------
# まとめて実行
# ---------------------------------------------------------------------------

def parse_all(full_lines: str) -> dict:
    """
    full_lines（全ページ結合・座標ベース）を受け取り、
    全フィールドを抽出して1つの dict で返す。
    """
    lines = [l for l in full_lines.split("\n") if l and not l.startswith("=== PAGE")]

    result = {}
    result.update(parse_basic(lines))
    result.update(parse_csr_ratings(lines))
    result.update(parse_flags(lines))
    result.update(parse_csr_structure(lines))
    result.update(parse_sri(lines))
    result.update(parse_shareholders(lines))
    result.update(parse_env_data(lines))
    return result
