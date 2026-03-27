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
        "TEL":        _first(r"【TEL】([\d\-－–()（）]+)", text),
        "EstblshYr":  _first(r"【設立】(\d[\d.]+)", text),
        "LstngYr":    _first(r"【上場】([\d.]+|―|-)", text),
        "AccntPrd":   _first(r"【決算期】(\S+)", text),
        # 長いキー名を先に試す（「本社」が「東京本社」より先にマッチするのを防ぐ）
        "cmpAdrs":    _first(r"【(?:東京本社|大阪本社|本店|本社)】([^\t\n]+)", text),
        "Chrctrstc":  _first(r"【特色】([^\t\n]+)", text),
    }


# ---------------------------------------------------------------------------
# CSR評価・財務評価スコア（ラベル行・レーティング行・スコア行の3行セット）
# ---------------------------------------------------------------------------

# CSR評価・財務評価で出現する固定ラベルセット（右カラム混入テキストの除外に使う）
_CSR_LABELS  = {"人材活用", "環境", "企業統治", "社会性", "基本"}
_FIN_LABELS  = {"成長性", "収益性", "安全性", "規模"}

# ラベル日本語 → 英語変数名プレフィックスの変換マップ
_LABEL_KEY = {
    "人材活用": "Hr",
    "環境":     "Env",
    "企業統治": "Gov",
    "社会性":   "Soc",
    "基本":     "Bsc",
    "成長性":   "Grwth",
    "収益性":   "Prft",
    "安全性":   "Sfty",
    "規模":     "Scl",
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
    prefix = "CSR" if header == "CSR評価" else "Fin"
    for i, label in enumerate(label_line):
        key = _LABEL_KEY.get(label, label)
        result[f"{prefix}{key}Rtng"] = rating_line[i] if rating_line and i < len(rating_line) else None
        result[f"{prefix}{key}Scr"]  = score_line[i]  if score_line  and i < len(score_line)  else None

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
    # --- CSR基本 ---
    "経営理念":                          "Prncpls",
    "活動のマテリアリティ設定":            "Mtralty",
    "ステークホルダー・エンゲージメント":   "StkhldrEnggmnt",
    "活動の報告":                        "RprtActvty",
    "第三者の関与":                      "Invlvmnt",
    "英文の報告書":                      "EngRprt",
    "統合報告書":                        "IntgrtRprt",
    "ESG情報の開示":                     "ESGInfrmtn",
    "機関投資家・ESG調査機関等との対話":   "ESGDialg",
    "SRIインデックス等への組み入れ":       "_sri_index_flag",  # parse_sri で上書き
    "ISO26000":                         "ISO26000",
    "汚職・贈収賄防止":                   "AntBrbry",
    "CSR調達の実施":                     "CSRPrcrmnt",
    "調達方針、労働方針、監査方針等の基準": "PrcrStndrd",
    "CSR調達に関する調達先監査・評価":     "CSRPrcrEvltn",
    "紛争鉱物の対応":                    "CnflctMnrl",
    "NPO・NGO連携":                     "NPOCollb",
    "SDGs":                             "SDGs",
    "BOPビジネスの取り組み":              "BOPBizEffrt",
    "CSV・BOPビジネスの位置づけ":         "CSVPlace",
    "コミュニティ投資の取り組み":          "CmmntyEffrt",
    "プロボノ支援の取り組み":             "ProbonoEffrt",
    # --- ガバナンス ---
    "株主の権利・平等性の確保":           "ShrhldrRght",
    "株主以外のステークホルダーとの適切な協働": "StkhldrCollb",
    "適切な情報開示と透明性の確保":        "Trnsprncy",
    "取締役会等の責務":                  "Rspnsblty",
    "株主との対話":                      "ShrhldrDialg",
    # --- 企業倫理・法令順守 ---
    "社員の行動規定":                    "CndctRule",
    "通報・告発者の権利保護規定":          "AccsrPrtct",
    "公益通報者保護法ガイドライン":        "PrtctGuide",
    # --- 内部統制 ---
    "内部監査部門":                      "IntrnlAdtDept",
    "内部統制の評価":                    "IntrnlCtrlEvltn",
    "CIO":                              "CIO",
    "CFO":                              "CFO",
    "情報セキュリティポリシー":            "ScrtyPlty",
    "ISMS":                             "ISMS",
    "プライバシー・ポリシー":             "PrvcyPlcy",
    "対応マニュアル":                    "RskMnal",
    "責任者":                           "RskMngr",
    "BCM構築":                          "BCMEstblsh",
    "BCP策定":                          "BCPSet",
    "BCP想定":                          "BCPAssmptn",
    # --- 消費者・品質 ---
    "クレーム対応":                      "Cmplint",
    # --- 社会貢献 ---
    "東日本大震災復興支援":               "JpnErthqkSpprt",
    # --- 環境：組織・情報開示 ---
    "HP上の公開":                        "HPOpen",
    "費用と効果／金額把握":               "CstEffct",
    "公開の有無":                        "Avlblty",
    "会計ベース":                        "AccntBase",
    "環境リスクマネジメントの取り組み":    "EnvRskMngmnt",
    "事業活動での環境汚染の危険性":        "EnvPlltn",
    "将来発生の可能性がある巨額費用の準備": "PrprHgExpns",
    "環境影響評価（アセスメント）":        "EnvAffctAssmnt",
    "土壌・地下水等の把握状況":           "Grndwtr",
    "水問題の認識":                      "WtrPrblm",
    "グリーン購入":                      "GrnBuy",
    "環境ラベリング":                    "EnvLblng",
    "環境ビジネスの取り組み":             "EnvBiz",
    "容器包装削減の取り組み":             "PckRduce",
    "カーボンオフセット商品等の取り組み":  "CrbnOffst",
    "気候変動対応の取り組み":             "ClimtEffrt",
    "再生可能エネルギーの導入":           "RnwablEnrgy",
    "CO2排出量等削減への中期計画":        "CO2Effrt",
    "生物多様性保全への取り組み":          "BioDvrstyEffrt",
    # --- 環境（既存） ---
    "環境会計":                          "EnvAccnt",
    "EMS構築":                          "EMSEstblsh",
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

    # 「方針の文書化・公開」と「方針の文書化】（CSR冒頭）」の2種類が混在するため、長いキーを優先
    result["CSRDcmntPlcy"] = (
        _first(r"【方針の文書化・公開】([^\t\n【]+)", text)
        or _first(r"【方針の文書化】([^\t\n【]+)", text)
    )
    result["MrlDcmnt"] = result["CSRDcmntPlcy"]  # 同値を企業倫理列にも設定

    # 法令順守セクション内の【部署】（LwCmplaDept）:
    m = re.search(r"法令順守[\s\S]{0,30}?【部署】([^\t\n【]+)", text)
    result["LwCmplaDept"] = m.group(1).strip() if m else None

    # IRセクション内の【部署】（IRDept）:
    m = re.search(r"\bIR\b[\s\S]{0,20}?【部署】([^\t\n【]+)", text)
    result["IRDept"] = m.group(1).strip() if m else None

    # 内部通報・告発窓口（AccstnHelp）:
    inner = _first(r"社内：\t([^\t\n]+)", text)
    outer = _first(r"社外：\t([^\t\n]+)", text)
    result["AccstnHelp"] = f"社内:{inner or '―'} 社外:{outer or '―'}" if (inner or outer) else None

    # CSR関連基準（CSRStndrd）
    result["CSRStndrd"] = _first(r"【CSR関連基準】([^\t\n【]+)", text)

    # 情報セキュリティ監査（ScrtyAdt）: 「内部：XX\t外部：XX」形式
    m = re.search(r"【情報セキュリティ監査】内部：([^\t\n]+)\t外部：([^\t\n【]+)", text)
    if m:
        result["ScrtyAdt"] = f"内部:{m.group(1).strip()} 外部:{m.group(2).strip()}"
    else:
        result["ScrtyAdt"] = _first(r"【情報セキュリティ監査】([^\t\n【]+)", text)

    # SRI重複回避: _sri_index_flag は parse_sri で上書きするため削除
    result.pop("_sri_index_flag", None)

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
        "CSRDeptTnr":  csr_dept_tenure,
        "CSRDept":     csr_dept_name,
        "CSROffcrTnr": csr_officer_tenure,
        "CSROffcr":    csr_officer_name,
        "CSRRetio":    csr_ratio,
    }


# ---------------------------------------------------------------------------
# SRIインデックス等への組み入れ
# ---------------------------------------------------------------------------

def parse_sri(lines: list[str]) -> dict:
    """
    SRIインデックス・エコファンドを取得する。
    """
    text = "\n".join(lines)
    return {
        "SRIIndx":   _first(r"【SRIインデックス等への組み入れ】([^\t\n【]+)", text),
        "SRIEcofnd": _first(r"【SRI、エコファンド等】([^\t\n【]+)", text),
    }


# ---------------------------------------------------------------------------
# 株主情報
# ---------------------------------------------------------------------------

def parse_shareholders(lines: list[str]) -> dict:
    text = "\n".join(lines)
    return {
        "NofShare":      _first(r"【株式数】([\d,]+)千株", text),
        "NofShrhldr":    _first(r"【株主総数】([\d,]+)人", text),
        "SpcfStckRatio": _first(r"【特定株比率】([\d.]+)%", text),
        "FlotStckRatio": _first(r"【浮動株比率】([\d.]+)%", text),
    }


# ---------------------------------------------------------------------------
# 環境負荷量（固定指標を個別に取得）
# ---------------------------------------------------------------------------
# 行形式: 指標名（単位）\t最新年度値\t前年度値
# 直近年度（最後の列）を取得する。欠損は None。

_ENV_METRICS = {
    "総エネルギー投入量":      "EnrgyGJ",
    "水資源投入量":            "WtrM3",
    "温室効果ガス排出量":      "GhgTco2",
    "特定化学物質排出量":      "ChemT",
    "廃棄物等総排出量":        "WasteT",
    "総排水量":               "WstwtrM3",
    "NOX":                   "NoxT",
    "SOX":                   "SoxT",
}

# スコープ3はセクションが独立しているため別途取得
_SCOPE3_METRIC = "温室効果ガス排出量"  # スコープ3セクション内の同名指標

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
# スコープ3・ISO取得率・環境コスト・生物多様性
# ---------------------------------------------------------------------------

def parse_env_tables(lines: list[str]) -> dict:
    """
    環境系のテーブル値を取得する。
    - EnvScp3  : スコープ3 温室効果ガス排出量（直近年度）
    - ISO14001 : 国内・海外の取得割合
    - ISO9000S : 国内・海外の取得割合
    - EnvCost  : 環境保全コスト合計（直近年度 費用額）
    - BioDvrstyPrjct: 生物多様性保全プロジェクト支出額（直近年度）
    """
    text = "\n".join(lines)
    result = {}

    # --- EnvScp3: 【スコープ3】直後の温室効果ガス排出量行（パターンA流用）---
    m = re.search(r"スコープ3[\s\S]{0,80}?温室効果ガス排出量[^\t\n]*\t([\d,]+)", text)
    result["EnvScp3"] = m.group(1) if m else None

    # --- ISO14001: 国内・海外取得割合（パターンA: 「国内\t値」形式）---
    m = re.search(r"【ISO14001】[\s\S]{0,60}?国内\t([\d.]+)", text)
    result["ISO14001Dom"] = m.group(1) if m else None
    m = re.search(r"【ISO14001】[\s\S]{0,120}?海外\t([\d.]+)", text)
    result["ISO14001Ovs"] = m.group(1) if m else None

    # --- ISO9000S: 国内・海外取得割合（パターンB: 「国内」次行に値）---
    for i, line in enumerate(lines):
        if "【ISO9000S】" not in line:
            continue
        dom = ovs = None
        for j in range(i + 1, min(i + 10, len(lines))):
            if re.fullmatch(r"国内", lines[j].strip()):
                if j + 1 < len(lines):
                    m = re.match(r"([\d.]+)", lines[j + 1].strip())
                    dom = m.group(1) if m else None
            elif re.fullmatch(r"海外", lines[j].strip()):
                if j + 1 < len(lines):
                    m = re.match(r"([\d.]+)", lines[j + 1].strip())
                    ovs = m.group(1) if m else None
        result["ISO9000SDom"] = dom
        result["ISO9000SOvs"] = ovs
        break

    # --- EnvCost: 環境保全コスト「合計」行の直近年度費用額 ---
    # 行形式: 「合計\t投資\t費用\t投資\t費用\t右カラム混在」→ タブ4番目が直近費用
    for line in lines:
        if not line.startswith("合計") or "環境保全コスト" in line:
            continue
        parts = [p.strip() for p in line.split("\t")]
        # 数値要素だけ抽出（カンマ区切り数値 or ―）
        nums = [p for p in parts[1:] if re.match(r"^[\d,]+$|^―$", p)]
        if len(nums) >= 4:
            result["EnvCost"] = nums[3]  # 直近年度費用額（4番目）
            break
        elif len(nums) >= 2:
            result["EnvCost"] = nums[-1]
            break
    else:
        result["EnvCost"] = None

    # --- BioDvrstyPrjct: 「支出額\t値\t値」の直近年度（パターンA: タブ後最後の数値）---
    m = re.search(r"支出額\t([\d,]+)\t([\d,]+)", text)
    result["BioDvrstyPrjct"] = m.group(2) if m else None

    return result


# ---------------------------------------------------------------------------
# 取締役・監査役人数
# ---------------------------------------------------------------------------

def parse_directors(lines: list[str]) -> dict:
    """
    取締役・監査役の各人数を抽出する。
    行形式（取締役直後の行）:
      「【特色】...テキスト...\t【人数】N人【代表者数】N人【女性役員】N人」
      「【社外取締役】N人」
    監査役:
      「【人数】N人【社外監査役】N人」
    """
    text = "\n".join(lines)

    # 取締役人数:
    # 【代表者数】と同行にある【人数】が取締役の人数（監査役行は【社外監査役】）
    m = re.search(r"【人数】(\d+)人【代表者数】", text)
    result = {"NofDrctr": m.group(1) if m else None}

    m = re.search(r"【代表者数】(\d+)人", text)
    result["NofCapDrctr"] = m.group(1) if m else None

    m = re.search(r"【女性役員】(\d+)人", text)
    result["NofWmDrctr"] = m.group(1) if m else None

    m = re.search(r"【社外取締役】(\d+)人", text)
    result["NofOutDrctr"] = m.group(1) if m else None

    # 監査役人数: 【社外監査役】と同行にある【人数】
    m = re.search(r"【人数】(\d+)人【社外監査役】", text)
    result["NofAdtr"] = m.group(1) if m else None

    m = re.search(r"【社外監査役】(\d+)人", text)
    result["NofOutAdtr"] = m.group(1) if m else None

    return result


# ---------------------------------------------------------------------------
# 通報件数・法令違反件数
# ---------------------------------------------------------------------------

def parse_compliance_counts(lines: list[str]) -> dict:
    """
    通報・告発件数（直近年度）と国内・海外法令違反件数を取得する。

    通報件数行: 「件数」→ 次行が年度値（別行）or「件数\t値\t値」（同行）
    国内法令違反: 「公取...排除勧告」等の行→次行「0\t0\t0」の最後の値
    海外法令違反: 「価格カルテルによる摘発」等→次行以降に1値ずつ
    """
    result = {}

    # --- NofAccstn: 通報件数（直近年度） ---
    for i, line in enumerate(lines):
        if "【通報・告発】" not in line:
            continue
        # 同行にタブ区切り数値があるか（パターンA）
        m = re.search(r"【通報・告発】[^\t\n]*\t[\d年度\s]+\t([\d]+)", line)
        if m:
            result["NofAccstn"] = m.group(1)
            break
        # 別行パターン: 「件数」行を探して次の数値行の最後を取る
        for j in range(i + 1, min(i + 8, len(lines))):
            if lines[j].strip() == "件数":
                # 件数の次の数値行群から最後の年度値を取る
                vals = []
                for k in range(j + 1, min(j + 5, len(lines))):
                    parts = [p for p in lines[k].split("\t") if re.match(r"^\d+$", p.strip())]
                    vals.extend(parts)
                    if not parts:
                        break
                result["NofAccstn"] = vals[-1] if vals else None
                break
        break
    else:
        result["NofAccstn"] = None

    # --- DmstcLwCase: 国内法令違反 各種件数の最新年度合計 ---
    # 「公取...排除勧告」「不祥事...操業停止」「コンプライアンス...刑事告発」の最新年度値を合算
    dmstc_keys = ["公取など関係官庁からの排除勧告", "不祥事などによる操業・営業停止",
                  "コンプライアンスに関わる事件・事故で刑事告発"]
    dmstc_total = 0
    dmstc_found = False
    for i, line in enumerate(lines):
        for key in dmstc_keys:
            if key not in line:
                continue
            # パターンA: 同行に「0\t0\t0」
            m = re.search(r"(\d+)\t(\d+)\t(\d+)", line)
            if m:
                dmstc_total += int(m.group(3))
                dmstc_found = True
            else:
                # パターンB: 次行以降に値が1つずつ
                vals = []
                for j in range(i + 1, min(i + 5, len(lines))):
                    s = lines[j].strip()
                    if re.fullmatch(r"\d+", s):
                        vals.append(int(s))
                    elif s and not re.match(r"\d", s):
                        break
                if vals:
                    dmstc_total += vals[-1]
                    dmstc_found = True
    result["DmstcLwCase"] = str(dmstc_total) if dmstc_found else None

    # --- OvrseaLwVioltn: 海外法令違反 各種件数の最新年度合計 ---
    ovrsea_keys = ["価格カルテルによる摘発", "贈賄による摘発", "その他の摘発"]
    ovrsea_total = 0
    ovrsea_found = False
    for i, line in enumerate(lines):
        for key in ovrsea_keys:
            if key not in line:
                continue
            m = re.search(r"(\d+)\t(\d+)\t(\d+)", line)
            if m:
                ovrsea_total += int(m.group(3))
                ovrsea_found = True
            else:
                vals = []
                for j in range(i + 1, min(i + 5, len(lines))):
                    s = lines[j].strip()
                    if re.fullmatch(r"\d+", s):
                        vals.append(int(s))
                    elif s and not re.match(r"\d", s):
                        break
                if vals:
                    ovrsea_total += vals[-1]
                    ovrsea_found = True
    result["OvrseaLwVioltn"] = str(ovrsea_total) if ovrsea_found else None

    return result


# ---------------------------------------------------------------------------
# 社会貢献・政治献金支出額
# ---------------------------------------------------------------------------

def parse_social_amounts(lines: list[str]) -> dict:
    """
    社会貢献活動支出額・政治献金支出額の直近年度総額を取得する。
    行形式: 「総額\t値1\t値2\t値3\t右カラム混在」→ 数値要素の最後が直近年度
    """
    result = {}

    for section, col in [("社会貢献活動支出額", "SclCntrbtnAmnt"),
                          ("政治献金・ロビー活動等支出額", "PltclCntrbtnAmnt")]:
        found = False
        for i, line in enumerate(lines):
            if section not in line:
                continue
            # 年度ヘッダ行（「14年度\t15年度\t16年度」等）から左カラムの列数を取得
            # タブ区切りで先頭から連続する年度トークン数のみ数える（右カラム混入を除外）
            n_years = None
            for j in range(i + 1, min(i + 4, len(lines))):
                parts = lines[j].split("\t")
                count = 0
                for p in parts:
                    if re.search(r"\d+年度", p):
                        count += 1
                    elif count > 0:
                        break  # 年度でないトークンが来たら終了
                if count > 0:
                    n_years = count
                    break
            # 「総額」行を最大6行以内で探す
            for j in range(i + 1, min(i + 7, len(lines))):
                if not lines[j].startswith("総額"):
                    continue
                parts = lines[j].split("\t")
                nums = [p.strip() for p in parts if re.match(r"^[\d,]+\.?\d*$", p.strip())]
                # 年度数が判明していれば先頭n_years個だけ取る（右カラム混入を排除）
                if n_years:
                    nums = nums[:n_years]
                if nums:
                    result[col] = nums[-1]  # 最後が直近年度
                    found = True
                break
            break
        if not found:
            result[col] = None

    return result


# ---------------------------------------------------------------------------
# グリーン購入比率・CO2削減等テキスト
# ---------------------------------------------------------------------------

def parse_env_efforts(lines: list[str]) -> dict:
    """
    事務用品等グリーン購入比率（直近年度）と
    CO2削減・リサイクル・廃棄物削減の取り組みテキストを取得する。
    """
    text = "\n".join(lines)
    result = {}

    # SpplyGrnBuy: 「比率（%）\t値\t値」の直近年度（タブ後最後の数値）
    # 行が右カラムに混在するため text から正規表現で取る
    m = re.search(r"比率（%）\t([\d.]+)\t([\d.]+)", text)
    result["SpplyGrnBuy"] = m.group(2) if m else None

    # CO2Rduce / Rcycl / WasteRduce:
    for key, col in [("CO2排出量等削減", "CO2Rduce"),
                     ("リサイクル",       "Rcycl"),
                     ("廃棄物削減",       "WasteRduce")]:
        # タブ混在で右カラムのテキストが混入するため、タブ前までを取得
        # キーが行後半にある場合も正規表現で拾う
        m = re.search(rf"【{re.escape(key)}】([^\t\n【]+)", text)
        if m:
            val = m.group(1).strip()
            # 続きが次行に切れているケース: 行末が「向」「達」等の途中で切れていれば次行を結合
            start = m.end()
            remaining = text[start:]
            extra = re.match(r"\n([^\t\n【＼①②③④⑤]+)", remaining)
            if extra and not re.match(r"^\s*(【|[A-Z]|[0-9]|NOX|SOX|水資源|温室|特定)", extra.group(1)):
                val = val + extra.group(1).strip()
            result[col] = val[:200]
        else:
            result[col] = None

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
    result.update(parse_env_tables(lines))
    result.update(parse_directors(lines))
    result.update(parse_compliance_counts(lines))
    result.update(parse_social_amounts(lines))
    result.update(parse_env_efforts(lines))
    return result
