"""申报义务与期限提示：需填表格 + 截止日（advisory rules）。

依据：个税法第 10–13 条；IRS Form 1040 / 1040-NR / W-9 / W-8BEN / 8833 / 8843 /
Schedule B / Schedule D / Form 8949 / 1116 / 8938 / FBAR (FinCEN 114) /
1099 系列 / 1042-S。
"""


def filing_obligations(cn_resident: bool, us_resident: bool, is_exempt_individual: bool = False) -> list:
    """根据中美税务身份返回主要申报义务、需填表格与期限。"""
    items = []

    # ================= 中国 =================
    if cn_resident:
        items.append({
            "zh": "综合所得汇算清缴",
            "en": "Annual comprehensive income settlement",
            "form": "个人所得税年度汇算清缴",
            "deadline": "次年 3 月 1 日 – 6 月 30 日",
            "cite": "个税法第 11 条",
        })
        items.append({
            "zh": "境外所得申报",
            "en": "Foreign income reporting",
            "form": "个人所得税境外所得申报",
            "deadline": "次年 3 月 1 日 – 6 月 30 日",
            "cite": "个税法第 13 条",
        })
    else:
        items.append({
            "zh": "非居民取得应税所得（无扣缴义务人）申报",
            "en": "Non-resident income filing (no withholding agent)",
            "form": "个人所得税申报表",
            "deadline": "取得所得次月 15 日内",
            "cite": "个税法第 13 条",
        })

    # ========== 美国：身份/预提证明（只要有美国来源所得就需提供，与报税无关）==========
    if us_resident:
        items.append({
            "zh": "向美国付款方提供纳税人识别号（TIN）",
            "en": "Provide taxpayer identification number to U.S. payers",
            "form": "Form W-9",
            "deadline": "首次付款前",
            "cite": "IRC §6109",
        })
    else:
        items.append({
            "zh": "向美国付款方证明外国身份并申请协定优惠（股息/版税降至 10%）",
            "en": "Certify foreign status and claim treaty benefits (dividend/royalty 10%)",
            "form": "Form W-8BEN",
            "deadline": "首次付款前（情况变更时更新）",
            "cite": "IRC §1441；中美协定第 9、11 条",
        })

    # ================= 美国：年度申报 =================
    if us_resident:
        items.append({
            "zh": "美国个人所得税申报",
            "en": "U.S. individual income tax return",
            "form": "Form 1040",
            "deadline": "次年 4 月 15 日",
            "cite": "IRC §6012",
        })
        items.append({
            "zh": "股息与利息申报",
            "en": "Report dividends and interest",
            "form": "Schedule B (Form 1040)",
            "deadline": "随 Form 1040 一并申报",
            "cite": "Form 1040 instructions",
        })
        items.append({
            "zh": "资本利得与亏损申报",
            "en": "Report capital gains and losses",
            "form": "Schedule D + Form 8949",
            "deadline": "随 Form 1040 一并申报",
            "cite": "IRC §1222",
        })
        items.append({
            "zh": "境外已纳税额抵免",
            "en": "Foreign tax credit",
            "form": "Form 1116",
            "deadline": "随 Form 1040 一并申报",
            "cite": "IRC §901",
        })
        items.append({
            "zh": "外国金融账户报告（合计 >1 万美元）",
            "en": "FBAR — foreign financial accounts",
            "form": "FinCEN Form 114",
            "deadline": "次年 4 月 15 日（自动延至 10 月 15 日）",
            "cite": "31 U.S.C. §5314",
        })
        items.append({
            "zh": "指定外国金融资产申报",
            "en": "Specified foreign financial assets (FATCA)",
            "form": "Form 8938",
            "deadline": "随 Form 1040 一并申报",
            "cite": "IRC §6038D",
        })
    else:
        items.append({
            "zh": "非居民外国人个人所得税申报",
            "en": "Nonresident alien income tax return",
            "form": "Form 1040-NR",
            "deadline": "次年 4 月 15 日（无工资预扣者 6 月 15 日）",
            "cite": "IRC §6012",
        })
        items.append({
            "zh": "协定优惠申报（如按协定主张待遇）",
            "en": "Treaty-based return position disclosure",
            "form": "Form 8833",
            "deadline": "随 Form 1040-NR 一并申报",
            "cite": "IRC §6114",
        })

    # ================= 豁免身份 =================
    if is_exempt_individual:
        items.append({
            "zh": "豁免身份申报（学生/教师/外交官，天数不计入实质停留测试）",
            "en": "Statement for exempt individuals",
            "form": "Form 8843",
            "deadline": "随申报表提交；无需报税者按报税截止日单独提交",
            "cite": "IRC §7701(b)",
        })

    return items


def information_returns(us_resident: bool) -> list:
    """你会收到的信息申报表（由付款方出具，非自行申报；advisory）。"""
    if us_resident:
        return [
            {"zh": "股息", "en": "Dividends", "form": "Form 1099-DIV", "note": "付款方次年 1 月 31 日前寄出"},
            {"zh": "利息", "en": "Interest", "form": "Form 1099-INT", "note": "付款方次年 1 月 31 日前寄出"},
            {"zh": "证券交易", "en": "Broker transactions", "form": "Form 1099-B", "note": "付款方次年 2 月 15 日前寄出"},
            {"zh": "非雇员报酬/版税", "en": "Non-employee compensation / royalties", "form": "Form 1099-NEC / 1099-MISC", "note": "付款方次年 1 月 31 日前寄出"},
        ]
    return [
        {"zh": "外国人在美所得（预提）", "en": "Foreign person's U.S. source income (withholding)", "form": "Form 1042-S", "note": "付款方次年 3 月 15 日前寄出"},
    ]
