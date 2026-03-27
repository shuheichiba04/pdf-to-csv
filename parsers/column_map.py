"""
CSV出力カラム定義。

COLUMNS は出力順に並んだ (内部キー, 英語変数名, 日本語ラベル) のリスト。
内部キーが複数ある場合（iso14001_dom/ovs 等）は結合処理を別途行う。
"""

# (内部キー or None, 英語変数名, 日本語ラベル)
COLUMNS = [
    # --- メタ ---
    ("file",                "File",             "ファイル名"),
    ("page_count",          "PageCount",        "ページ数"),
    ("text_quality",        "TextQuality",      "テキスト品質"),
    ("error",               "Error",            "エラー"),

    # --- 基本情報 ---
    ("established",         "EstblshYr",        "設立年月"),
    ("listed",              "LstngYr",          "上場年月"),
    ("fiscal_end",          "AccntPrd",         "決算期"),
    ("address",             "cmpAdrs",          "本社住所"),
    ("tel",                 "TEL",              "TEL"),
    ("description",         "Chrctrstc",        "特色"),

    # --- CSR評価 ---
    ("csr_hr_rating",       "CSRHrRtng",        "CSR評価_人材活用_レーティング"),
    ("csr_hr_score",        "CSRHrScr",         "CSR評価_人材活用_スコア"),
    ("csr_env_rating",      "CSREnvRtng",       "CSR評価_環境_レーティング"),
    ("csr_env_score",       "CSREnvScr",        "CSR評価_環境_スコア"),
    ("csr_gov_rating",      "CSRGovRtng",       "CSR評価_企業統治_レーティング"),
    ("csr_gov_score",       "CSRGovScr",        "CSR評価_企業統治_スコア"),
    ("csr_soc_rating",      "CSRSocRtng",       "CSR評価_社会性_レーティング"),
    ("csr_soc_score",       "CSRSocScr",        "CSR評価_社会性_スコア"),
    ("csr_bsc_rating",      "CSRBscRtng",       "CSR評価_基本_レーティング"),
    ("csr_bsc_score",       "CSRBscScr",        "CSR評価_基本_スコア"),

    # --- 財務評価 ---
    ("fin_grwth_rating",    "FinGrwthRtng",     "財務評価_成長性_レーティング"),
    ("fin_grwth_score",     "FinGrwthScr",      "財務評価_成長性_スコア"),
    ("fin_prft_rating",     "FinPrftRtng",      "財務評価_収益性_レーティング"),
    ("fin_prft_score",      "FinPrftScr",       "財務評価_収益性_スコア"),
    ("fin_sfty_rating",     "FinSftyRtng",      "財務評価_安全性_レーティング"),
    ("fin_sfty_score",      "FinSftyScr",       "財務評価_安全性_スコア"),
    ("fin_scl_rating",      "FinSclRtng",       "財務評価_規模_レーティング"),
    ("fin_scl_score",       "FinSclScr",        "財務評価_規模_スコア"),

    # --- CSR基本 ---
    ("has_philosophy",      "Prncpls",          "経営理念"),
    ("has_materiality",     "Mtralty",          "活動のマテリアリティ設定"),
    ("csr_policy_doc",      "CSRDcmntPlcy",     "CSR方針の文書化"),
    ("activity_report",     "RprtActvty",       "活動の報告"),
    ("has_third_party",     "Invlvmnt",         "第三者の関与"),
    ("has_eng_report",      "EngRprt",          "英文の報告書"),
    ("has_integrated_report","IntgrtRprt",      "統合報告書"),
    ("stakeholder_engagement","StkhldrEnggmnt", "ステークホルダーエンゲージメント"),
    ("anti_corruption_policy","AntBrbry",       "汚職贈収賄防止"),
    ("iso26000",            "ISO26000",         "ISO26000"),
    ("csr_dept_tenure",     "CSRDeptTnr",       "CSR部署_専任兼任"),
    ("csr_dept_name",       "CSRDept",          "CSR部署"),
    ("csr_officer_tenure",  "CSROffcrTnr",      "CSR担当役員_専任兼任"),
    ("csr_officer_name",    "CSROffcr",         "CSR担当役員"),
    ("csr_ratio",           "CSRRetio",         "同CSR業務比率"),
    ("npo_ngo",             "NPOCollb",         "NPONGO連携"),
    ("csr_stndrd",          "CSRStndrd",        "CSR関連基準"),
    ("esg_disclosure",      "ESGInfrmtn",       "ESG情報の開示"),
    ("esg_investor_dialog", "ESGDialg",         "機関投資家ESG調査機関等との対話"),
    ("sri_index",           "SRIIndx",          "SRIインデックス等への組み入れ"),
    ("sri_ecofnd",          "SRIEcofnd",        "SRIエコファンド等"),

    # --- ガバナンス ---
    ("shrhldr_rght",        "ShrhldrRght",      "株主の権利平等性の確保"),
    ("stkhldr_collb",       "StkhldrCollb",     "株主以外のステークホルダーとの適切な協働"),
    ("trnsprncy",           "Trnsprncy",        "適切な情報開示と透明性の確保"),
    ("rspnsblty",           "Rspnsblty",        "取締役会等の責務"),
    ("shrhldr_dialg",       "ShrhldrDialg",     "株主との対話"),

    # --- CSR調達 ---
    ("csr_procurement",     "CSRPrcrmnt",       "CSR調達の実施"),
    ("csr_procr_stndrd",    "PrcrStndrd",       "調達方針、労働方針、監査方針等の基準"),
    ("csr_procr_evltn",     "CSRPrcrEvltn",     "CSR調達に関する調達先監査・評価"),
    ("cnflct_mnrl",         "CnflctMnrl",       "紛争鉱物の対応"),

    # --- SDGs/CSV/BOP/コミュニティ ---
    ("sdgs",                "SDGs",             "SDGs"),
    ("bop_biz_effrt",       "BOPBizEffrt",      "BOPビジネスの取り組み"),
    ("csv_place",           "CSVPlace",         "CSVBOPビジネスの位置づけ"),
    ("cmmnty_effrt",        "CmmntyEffrt",      "コミュニティ投資の取り組み"),
    ("probono_effrt",       "ProbonoEffrt",     "プロボノ支援の取り組み"),
    ("jpn_erth_spprt",      "JpnErthqkSpprt",  "東日本大震災復興支援"),

    # --- 取締役・監査役・株主 ---
    ("n_drctr",             "NofDrctr",         "取締役人数"),
    ("n_cap_drctr",         "NofCapDrctr",      "取締役代表者数"),
    ("n_wm_drctr",          "NofWmDrctr",       "取締役女性役員"),
    ("n_out_drctr",         "NofOutDrctr",      "社外取締役"),
    ("n_adtr",              "NofAdtr",          "監査役人数"),
    ("n_out_adtr",          "NofOutAdtr",       "社外監査役"),
    ("shares_total",        "NofShare",         "株式数"),
    ("shareholders_n",      "NofShrhldr",       "株主総数"),
    ("major_share_pct",     "SpcfStckRatio",    "特定株比率"),
    ("float_pct",           "FlotStckRatio",    "浮動株比率"),

    # --- 企業倫理・法令順守 ---
    ("csr_policy_doc",      "MrlDcmnt",         "企業倫理方針の文書化"),
    ("cndct_rule",          "CndctRule",        "社員行動規定"),
    ("lw_compla_dept",      "LwCmplaDept",      "法令順守部署"),
    ("ir_dept",             "IRDept",           "IR部署"),
    ("accstn_help",         "AccstnHelp",       "内部通報告発窓口"),
    ("accsr_prtct",         "AccsrPrtct",       "通報告発者の権利保護規定"),
    ("prtct_guide",         "PrtctGuide",       "公益通報者保護法ガイドライン"),
    ("n_accstn",            "NofAccstn",        "通報告発数"),
    ("dmstc_lw_case",       "DmstcLwCase",      "国内法令等関連事件"),
    ("ovrsea_lw_violtn",    "OvrseaLwVioltn",   "海外法令違反"),

    # --- 内部統制・セキュリティ・リスク ---
    ("internal_audit",      "IntrnlAdtDept",    "内部監査部門"),
    ("intrnl_ctrl_evltn",   "IntrnlCtrlEvltn",  "内部統制の評価"),
    ("cio",                 "CIO",              "CIO"),
    ("cfo",                 "CFO",              "CFO"),
    ("scrty_plty",          "ScrtyPlty",        "情報セキュリティポリシー"),
    ("scrty_adt",           "ScrtyAdt",         "情報セキュリティ監査"),
    ("isms",                "ISMS",             "ISMS"),
    ("prvcyplcy",           "PrvcyPlcy",        "プライバシーポリシー"),
    ("rsk_mnal",            "RskMnal",          "リスク対応マニュアル"),
    ("rsk_mngr",            "RskMngr",          "リスクマネ責任者"),
    ("bcm",                 "BCMEstblsh",       "BCM構築"),
    ("bcp",                 "BCPSet",           "BCP策定"),
    ("bcp_assmptn",         "BCPAssmptn",       "BCP想定"),

    # --- 消費者・品質 ---
    ("cmplint",             "Cmplint",          "クレーム対応"),
    ("iso9000s_dom",        "ISO9000SDom",      "ISO9000S_国内取得割合"),
    ("iso9000s_ovs",        "ISO9000SOvs",      "ISO9000S_海外取得割合"),

    # --- 社会貢献 ---
    ("scl_cntrbtn_amnt",    "SclCntrbtnAmnt",   "社会貢献活動支出額"),
    ("pltcl_cntrbtn_amnt",  "PltclCntrbtnAmnt", "政治献金ロビー活動等支出額"),

    # --- 環境：組織・情報開示 ---
    ("hp_open",             "HPOpen",           "HP上の公開"),
    ("env_accounting",      "EnvAccnt",         "環境会計"),
    ("cst_effct",           "CstEffct",         "費用と効果金額把握"),
    ("avlblty",             "Avlblty",          "公開の有無"),
    ("accnt_base",          "AccntBase",        "会計ベース"),
    ("env_cost",            "EnvCost",          "環境保全コスト"),
    ("ems",                 "EMSEstblsh",       "EMS構築"),
    ("iso14001_dom",        "ISO14001Dom",      "ISO14001_国内取得割合"),
    ("iso14001_ovs",        "ISO14001Ovs",      "ISO14001_海外取得割合"),

    # --- 環境負荷量 ---
    ("energy_gj",           "EnrgyGJ",          "総エネルギー投入量(GJ)"),
    ("water_m3",            "WtrM3",            "水資源投入量(m3)"),
    ("ghg_tco2",            "GhgTco2",          "温室効果ガス排出量(t-CO2)"),
    ("chemical_t",          "ChemT",            "特定化学物質排出量(t)"),
    ("waste_t",             "WasteT",           "廃棄物等総排出量(t)"),
    ("wastewater_m3",       "WstwtrM3",         "総排水量(m3)"),
    ("nox_t",               "NoxT",             "NOX(t)"),
    ("sox_t",               "SoxT",             "SOX(t)"),
    ("env_scp3",            "EnvScp3",          "スコープ3温室効果ガス排出量(t-CO2)"),

    # --- 環境：リスク・法規制 ---
    ("env_rsk_mngmnt",      "EnvRskMngmnt",     "環境リスクマネジメントの取り組み"),
    ("env_plltn",           "EnvPlltn",         "事業活動での環境汚染の危険性"),
    ("prpr_hg_expns",       "PrprHgExpns",      "将来発生の可能性がある巨額費用の準備"),
    ("env_affct_assmnt",    "EnvAffctAssmnt",   "環境影響評価アセスメント"),
    ("grndwtr",             "Grndwtr",          "土壌地下水等の把握状況"),
    ("wtr_prblm",           "WtrPrblm",         "水問題の認識"),

    # --- 環境：施策・取り組み ---
    ("grn_buy",             "GrnBuy",           "グリーン購入"),
    ("spply_grn_buy",       "SpplyGrnBuy",      "事務用品等のグリーン購入"),
    ("env_lblng",           "EnvLblng",         "環境ラベリング"),
    ("env_biz",             "EnvBiz",           "環境ビジネスの取り組み"),
    ("pck_reduce",          "PckRduce",         "容器包装削減の取り組み"),
    ("crbn_offst",          "CrbnOffst",        "カーボンオフセット商品等の取り組み"),
    ("climt_effrt",         "ClimtEffrt",       "気候変動対応の取り組み"),
    ("rnwabl_enrgy",        "RnwablEnrgy",      "再生可能エネルギーの導入"),
    ("co2_effrt",           "CO2Effrt",         "CO2排出量等削減への中期計画"),
    ("bio_dvrsty_effrt",    "BioDvrstyEffrt",   "生物多様性保全への取り組み"),
    ("bio_dvrsty_prjct",    "BioDvrstyPrjct",   "生物多様性保全プロジェクト"),
    ("co2_rduce",           "CO2Rduce",         "CO2排出量等削減実績"),
    ("enrgy_rduce",         "Rcycl",            "リサイクル"),
    ("waste_rduce",         "WasteRduce",       "廃棄物削減"),
]

# 重複チェック用: 同じ内部キーが複数エントリに使われている場合は両方出力する
# (csr_policy_doc は MrlDcmnt と CSRDcmntPlcy に重複使用)


def apply_column_map(rows: list[dict]) -> tuple[list[str], list[str], list[list]]:
    """
    rows（parse_all の出力リスト）に対してカラムマッピングを適用する。

    戻り値:
        jp_labels  : 1行目（日本語ラベル）のリスト
        en_names   : 2行目（英語変数名）のリスト
        data_rows  : データ行のリスト（各行は値のリスト）
    """
    jp_labels = [jp  for _, _, jp  in COLUMNS]
    en_names  = [en  for _, en, _   in COLUMNS]
    data_rows = []
    for row in rows:
        data_rows.append([row.get(internal) for internal, _, _ in COLUMNS])
    return jp_labels, en_names, data_rows
