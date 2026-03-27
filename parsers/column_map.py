"""
CSV出力カラム定義。

COLUMNS は出力順に並んだ (英語変数名, 日本語ラベル) のリスト。
英語変数名は parse_all() が返す dict のキーと一致する。
"""

# (英語変数名, 日本語ラベル)
COLUMNS = [
    # --- メタ ---
    ("File",             "ファイル名"),
    ("PageCount",        "ページ数"),
    ("TextQuality",      "テキスト品質"),
    ("Error",            "エラー"),

    # --- 基本情報 ---
    ("EstblshYr",        "設立年月"),
    ("LstngYr",          "上場年月"),
    ("AccntPrd",         "決算期"),
    ("cmpAdrs",          "本社住所"),
    ("TEL",              "TEL"),
    ("Chrctrstc",        "特色"),

    # --- CSR評価 ---
    ("CSRHrRtng",        "CSR評価_人材活用_レーティング"),
    ("CSRHrScr",         "CSR評価_人材活用_スコア"),
    ("CSREnvRtng",       "CSR評価_環境_レーティング"),
    ("CSREnvScr",        "CSR評価_環境_スコア"),
    ("CSRGovRtng",       "CSR評価_企業統治_レーティング"),
    ("CSRGovScr",        "CSR評価_企業統治_スコア"),
    ("CSRSocRtng",       "CSR評価_社会性_レーティング"),
    ("CSRSocScr",        "CSR評価_社会性_スコア"),
    ("CSRBscRtng",       "CSR評価_基本_レーティング"),
    ("CSRBscScr",        "CSR評価_基本_スコア"),

    # --- 財務評価 ---
    ("FinGrwthRtng",     "財務評価_成長性_レーティング"),
    ("FinGrwthScr",      "財務評価_成長性_スコア"),
    ("FinPrftRtng",      "財務評価_収益性_レーティング"),
    ("FinPrftScr",       "財務評価_収益性_スコア"),
    ("FinSftyRtng",      "財務評価_安全性_レーティング"),
    ("FinSftyScr",       "財務評価_安全性_スコア"),
    ("FinSclRtng",       "財務評価_規模_レーティング"),
    ("FinSclScr",        "財務評価_規模_スコア"),

    # --- CSR基本 ---
    ("Prncpls",          "経営理念"),
    ("Mtralty",          "活動のマテリアリティ設定"),
    ("CSRDcmntPlcy",     "CSR方針の文書化"),
    ("RprtActvty",       "活動の報告"),
    ("Invlvmnt",         "第三者の関与"),
    ("EngRprt",          "英文の報告書"),
    ("IntgrtRprt",       "統合報告書"),
    ("StkhldrEnggmnt",   "ステークホルダーエンゲージメント"),
    ("AntBrbry",         "汚職贈収賄防止"),
    ("ISO26000",         "ISO26000"),
    ("CSRDeptTnr",       "CSR部署_専任兼任"),
    ("CSRDept",          "CSR部署"),
    ("CSROffcrTnr",      "CSR担当役員_専任兼任"),
    ("CSROffcr",         "CSR担当役員"),
    ("CSRRetio",         "同CSR業務比率"),
    ("NPOCollb",         "NPONGO連携"),
    ("CSRStndrd",        "CSR関連基準"),
    ("ESGInfrmtn",       "ESG情報の開示"),
    ("ESGDialg",         "機関投資家ESG調査機関等との対話"),
    ("SRIIndx",          "SRIインデックス等への組み入れ"),
    ("SRIEcofnd",        "SRIエコファンド等"),

    # --- ガバナンス ---
    ("ShrhldrRght",      "株主の権利平等性の確保"),
    ("StkhldrCollb",     "株主以外のステークホルダーとの適切な協働"),
    ("Trnsprncy",        "適切な情報開示と透明性の確保"),
    ("Rspnsblty",        "取締役会等の責務"),
    ("ShrhldrDialg",     "株主との対話"),

    # --- CSR調達 ---
    ("CSRPrcrmnt",       "CSR調達の実施"),
    ("PrcrStndrd",       "調達方針、労働方針、監査方針等の基準"),
    ("CSRPrcrEvltn",     "CSR調達に関する調達先監査・評価"),
    ("CnflctMnrl",       "紛争鉱物の対応"),

    # --- SDGs/CSV/BOP/コミュニティ ---
    ("SDGs",             "SDGs"),
    ("BOPBizEffrt",      "BOPビジネスの取り組み"),
    ("CSVPlace",         "CSVBOPビジネスの位置づけ"),
    ("CmmntyEffrt",      "コミュニティ投資の取り組み"),
    ("ProbonoEffrt",     "プロボノ支援の取り組み"),
    ("JpnErthqkSpprt",   "東日本大震災復興支援"),

    # --- 取締役・監査役・株主 ---
    ("NofDrctr",         "取締役人数"),
    ("NofCapDrctr",      "取締役代表者数"),
    ("NofWmDrctr",       "取締役女性役員"),
    ("NofOutDrctr",      "社外取締役"),
    ("NofAdtr",          "監査役人数"),
    ("NofOutAdtr",       "社外監査役"),
    ("NofShare",         "株式数"),
    ("NofShrhldr",       "株主総数"),
    ("SpcfStckRatio",    "特定株比率"),
    ("FlotStckRatio",    "浮動株比率"),

    # --- 企業倫理・法令順守 ---
    ("MrlDcmnt",         "企業倫理方針の文書化"),
    ("CndctRule",        "社員行動規定"),
    ("LwCmplaDept",      "法令順守部署"),
    ("IRDept",           "IR部署"),
    ("AccstnHelp",       "内部通報告発窓口"),
    ("AccsrPrtct",       "通報告発者の権利保護規定"),
    ("PrtctGuide",       "公益通報者保護法ガイドライン"),
    ("NofAccstn",        "通報告発数"),
    ("DmstcLwCase",      "国内法令等関連事件"),
    ("OvrseaLwVioltn",   "海外法令違反"),

    # --- 内部統制・セキュリティ・リスク ---
    ("IntrnlAdtDept",    "内部監査部門"),
    ("IntrnlCtrlEvltn",  "内部統制の評価"),
    ("CIO",              "CIO"),
    ("CFO",              "CFO"),
    ("ScrtyPlty",        "情報セキュリティポリシー"),
    ("ScrtyAdt",         "情報セキュリティ監査"),
    ("ISMS",             "ISMS"),
    ("PrvcyPlcy",        "プライバシーポリシー"),
    ("RskMnal",          "リスク対応マニュアル"),
    ("RskMngr",          "リスクマネ責任者"),
    ("BCMEstblsh",       "BCM構築"),
    ("BCPSet",           "BCP策定"),
    ("BCPAssmptn",       "BCP想定"),

    # --- 消費者・品質 ---
    ("Cmplint",          "クレーム対応"),
    ("ISO9000SDom",      "ISO9000S_国内取得割合"),
    ("ISO9000SOvs",      "ISO9000S_海外取得割合"),

    # --- 社会貢献 ---
    ("SclCntrbtnAmnt",   "社会貢献活動支出額"),
    ("PltclCntrbtnAmnt", "政治献金ロビー活動等支出額"),

    # --- 環境：組織・情報開示 ---
    ("HPOpen",           "HP上の公開"),
    ("EnvAccnt",         "環境会計"),
    ("CstEffct",         "費用と効果金額把握"),
    ("Avlblty",          "公開の有無"),
    ("AccntBase",        "会計ベース"),
    ("EnvCost",          "環境保全コスト"),
    ("EMSEstblsh",       "EMS構築"),
    ("ISO14001Dom",      "ISO14001_国内取得割合"),
    ("ISO14001Ovs",      "ISO14001_海外取得割合"),

    # --- 環境負荷量 ---
    ("EnrgyGJ",          "総エネルギー投入量(GJ)"),
    ("WtrM3",            "水資源投入量(m3)"),
    ("GhgTco2",          "温室効果ガス排出量(t-CO2)"),
    ("ChemT",            "特定化学物質排出量(t)"),
    ("WasteT",           "廃棄物等総排出量(t)"),
    ("WstwtrM3",         "総排水量(m3)"),
    ("NoxT",             "NOX(t)"),
    ("SoxT",             "SOX(t)"),
    ("EnvScp3",          "スコープ3温室効果ガス排出量(t-CO2)"),

    # --- 環境：リスク・法規制 ---
    ("EnvRskMngmnt",     "環境リスクマネジメントの取り組み"),
    ("EnvPlltn",         "事業活動での環境汚染の危険性"),
    ("PrprHgExpns",      "将来発生の可能性がある巨額費用の準備"),
    ("EnvAffctAssmnt",   "環境影響評価アセスメント"),
    ("Grndwtr",          "土壌地下水等の把握状況"),
    ("WtrPrblm",         "水問題の認識"),

    # --- 環境：施策・取り組み ---
    ("GrnBuy",           "グリーン購入"),
    ("SpplyGrnBuy",      "事務用品等のグリーン購入"),
    ("EnvLblng",         "環境ラベリング"),
    ("EnvBiz",           "環境ビジネスの取り組み"),
    ("PckRduce",         "容器包装削減の取り組み"),
    ("CrbnOffst",        "カーボンオフセット商品等の取り組み"),
    ("ClimtEffrt",       "気候変動対応の取り組み"),
    ("RnwablEnrgy",      "再生可能エネルギーの導入"),
    ("CO2Effrt",         "CO2排出量等削減への中期計画"),
    ("BioDvrstyEffrt",   "生物多様性保全への取り組み"),
    ("BioDvrstyPrjct",   "生物多様性保全プロジェクト"),
    ("CO2Rduce",         "CO2排出量等削減実績"),
    ("Rcycl",            "リサイクル"),
    ("WasteRduce",       "廃棄物削減"),
]


def apply_column_map(rows: list[dict]) -> tuple[list[str], list[str], list[list]]:
    """
    rows（parse_all の出力リスト）に対してカラムマッピングを適用する。

    戻り値:
        jp_labels  : 1行目（日本語ラベル）のリスト
        en_names   : 2行目（英語変数名）のリスト
        data_rows  : データ行のリスト（各行は値のリスト）
    """
    en_names  = [en for en, _  in COLUMNS]
    jp_labels = [jp for _,  jp in COLUMNS]
    data_rows = [
        [row.get(en) for en, _ in COLUMNS]
        for row in rows
    ]
    return jp_labels, en_names, data_rows
