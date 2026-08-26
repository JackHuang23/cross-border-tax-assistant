"""跨境个人税务助理 · Flask Web 应用（单页 + JSON API）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, render_template, request, send_from_directory

from tax_engine import (
    determine_china_residency,
    determine_us_residency,
    tie_breaker,
    us_countable_days,
    resident_comprehensive_taxable,
    china_resident_comprehensive_tax,
    china_dividend_tax,
    china_dividend_tax_bucketed,
    china_a_share_capital_gain_tax,
    us_nra_dividend_tax,
    us_nra_capital_gain_tax,
    us_long_term_capital_gains_rate,
    us_resident_dividend_tax,
    foreign_tax_credit_limit,
    us_ordinary_tax,
    us_royalty_withholding_tax,
    cross_border_service_taxability,
    cross_border_royalty_treatment,
    filing_obligations,
    information_returns,
)
from tax_engine import constants as C

def _base_dir():
    """资源根目录；兼容 PyInstaller 打包（sys._MEIPASS 临时解包目录）。"""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.dirname(os.path.abspath(__file__))


app = Flask(
    __name__,
    template_folder=os.path.join(_base_dir(), "templates"),
    static_folder=os.path.join(_base_dir(), "static"),
)


def _f(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


@app.route("/")
def index():
    return render_template("index.html")


DOCS_DIR = os.path.join(_base_dir(), "docs")


@app.route("/legal-basis")
def legal_basis():
    """内置《法条依据》全文（HTML，离线可看）。"""
    return send_from_directory(DOCS_DIR, "法条依据.html")


@app.route("/api/calculate", methods=["POST"])
def calculate():
    data = request.get_json(force=True) or {}

    # ---------- 中国身份 ----------
    cn = data.get("china", {})
    cn_res = determine_china_residency(
        has_domicile=bool(cn.get("has_domicile")),
        full_24h_days_cn=int(_f(cn.get("full_24h_days"))),
        consecutive_qualifying_years=int(_f(cn.get("consecutive_qualifying_years"))),
    )

    # ---------- 美国身份 ----------
    us = data.get("us", {})
    is_gc = bool(us.get("is_citizen_or_gc"))
    ex = us.get("exclusions", {}) or {}
    exclusions = {
        "commuter": int(_f(ex.get("commuter"))),
        "transit_under_24h": int(_f(ex.get("transit_under_24h"))),
        "crew": int(_f(ex.get("crew"))),
        "medical": int(_f(ex.get("medical"))),
        "exempt": int(_f(ex.get("exempt"))),
    }
    us_exempt_type = us.get("exempt_type", "none")  # 豁免身份类型（A/G外交官、J/Q教师、F/J/M/Q学生等）

    def _days(gross):
        # 天数口径：美国「任何一天在境内都算 1 天」，减去 5 类例外
        return us_countable_days(
            int(_f(gross)),
            commuter_days=exclusions["commuter"],
            transit_under_24h=exclusions["transit_under_24h"],
            crew_days=exclusions["crew"],
            medical_days=exclusions["medical"],
            exempt_days=exclusions["exempt"],
        )

    days_cur = _days(us.get("gross_days_current"))
    days_p1 = _days(us.get("gross_days_prev1"))
    days_p2 = _days(us.get("gross_days_prev2"))
    us_res = determine_us_residency(is_gc, days_cur, days_p1, days_p2)

    # ---------- 双重居民（仅双方居民时） ----------
    tb_result = None
    if cn_res.is_resident and us_res.is_resident:
        tb_result = tie_breaker()

    # ================= 收入解析（4 类 × 双边来源） =================
    inc = data.get("income", {}) or {}
    div_cn = _f(inc.get("dividend_cn"))   # 中国来源股息红利
    div_us = _f(inc.get("dividend_us"))   # 美国来源股息红利
    cg_cn = _f(inc.get("cg_cn"))          # 中国来源资本利得（A股，暂免）
    st_gain = _f(inc.get("st_gain"))      # 短期资本利得（美股，逐笔）
    lt_gain = _f(inc.get("lt_gain"))      # 长期资本利得（美股，逐笔）
    _manual_cg_us = _f(inc.get("cg_us"))  # 手动美国资本利得（无逐笔时回退，视为长期）
    if st_gain == 0 and lt_gain == 0:
        lt_gain = _manual_cg_us
    us_cg_total = st_gain + lt_gain       # 美国来源资本利得总额
    sal_cn = _f(inc.get("salary_cn"))     # 中国来源工资薪金
    sal_us = _f(inc.get("salary_us"))     # 美国来源工资薪金
    svc_cn = _f(inc.get("service_cn"))    # 中国来源劳务报酬
    svc_us = _f(inc.get("service_us"))    # 美国来源劳务报酬
    roy_cn = _f(inc.get("royalty_cn"))    # 中国来源版税
    roy_us = _f(inc.get("royalty_us"))    # 美国来源版税

    cn_holding = inc.get("cn_holding_months")
    cn_holding = _f(cn_holding) if cn_holding not in (None, "") else None
    us_holding_days = int(_f(inc.get("us_holding_days")))
    us_taxable_income = _f(inc.get("us_taxable_income"))
    special_deduction = _f(inc.get("special_deduction"))
    special_additional = _f(inc.get("special_additional"))

    # 逐笔持仓股息分桶（前端按持有期分好）
    div_cn_lte_1m = _f(inc.get("div_cn_lte_1m"))
    div_cn_1m_12m = _f(inc.get("div_cn_1m_12m"))
    div_cn_gt_1y = _f(inc.get("div_cn_gt_1y"))
    div_qualified = _f(inc.get("div_qualified"))
    div_nonqualified = _f(inc.get("div_nonqualified"))
    has_cn_buckets = (div_cn_lte_1m + div_cn_1m_12m + div_cn_gt_1y) > 0
    has_us_buckets = (div_qualified + div_nonqualified) > 0

    def _comp(sal, svc, roy):
        # 综合所得收入额 = 工资×100% + 劳务×80% + 版税×80%（稿酬×56% 并入版税近似）
        return sal + svc * 0.8 + roy * 0.8

    # ================= 中国税 =================
    cn_comp_cn = _comp(sal_cn, svc_cn, roy_cn)
    cn_comp_us = _comp(sal_us, svc_us, roy_us)
    # 中国股息红利税：逐笔持仓按持有期分桶，否则按单一持有期回退
    if has_cn_buckets:
        cn_div_tax = china_dividend_tax_bucketed(div_cn_lte_1m, div_cn_1m_12m, div_cn_gt_1y)
    else:
        cn_div_tax = china_dividend_tax(div_cn, True, cn_holding)
    if cn_res.is_resident:
        worldwide = cn_comp_cn + (cn_comp_us if cn_res.six_year_rule_triggered else 0.0)
        cn_taxable = max(0.0, worldwide - C.CN_RESIDENT_BASIC_DEDUCTION - special_deduction - special_additional)
        cn_comprehensive_tax = china_resident_comprehensive_tax(cn_taxable)
        cn_cg_tax = 0.0  # A 股转让暂免（财税字〔1998〕61 号）
        if cn_res.six_year_rule_triggered:
            cn_div_tax = round(cn_div_tax + div_us * C.CN_OTHER_RATE, 2)  # 境外股息 20%
            cn_cg_tax = round(us_cg_total * C.CN_OTHER_RATE, 2)                 # 境外资本利得 20%
    else:
        cn_taxable = max(0.0, cn_comp_cn - C.CN_RESIDENT_BASIC_DEDUCTION - special_deduction - special_additional)
        cn_comprehensive_tax = china_resident_comprehensive_tax(cn_taxable)
        cn_cg_tax = 0.0
    cn_total_tax = round(cn_comprehensive_tax + cn_div_tax + cn_cg_tax, 2)

    # ================= 美国税 =================
    us_ordinary_gross = sal_cn + sal_us + svc_cn + svc_us + roy_cn + roy_us + st_gain
    # 若用户未填「美国应纳税所得额」，则用其他输入估算（用于 LTCG 税率档判定）
    if us_taxable_income <= 0:
        us_taxable_income = max(0.0, us_ordinary_gross + lt_gain + div_cn + div_us)
    us_total_tax = 0.0
    us_ordinary_tax_val = 0.0
    us_div_tax = 0.0
    us_cg_tax = 0.0
    us_se_tax = 0.0
    us_service_tax = 0.0
    us_royalty_tax = 0.0
    us_notes = []
    cb_service = None
    cb_royalty = None

    if us_res.is_resident:
        # 全球征税（worldwide）
        if svc_us > 0:
            se_base = svc_us * 0.9235
            if se_base >= 400:
                us_se_tax = round(min(se_base, C.US_SS_WAGE_BASE_2026) * 0.124 + se_base * 0.029, 2)
        # 股息：合格（>60 天）按 LTCG；非合格并入普通所得（逐笔持仓分桶，否则单一持有期回退）
        if has_us_buckets:
            qualified_div = div_qualified
            nonqualified_div = div_nonqualified
        else:
            _div_total = div_cn + div_us
            _q = us_holding_days > C.US_QUALIFIED_DIVIDEND_HOLDING_DAYS
            qualified_div = _div_total if _q else 0.0
            nonqualified_div = 0.0 if _q else _div_total
        us_ordinary_taxable = max(0.0, us_ordinary_gross + nonqualified_div - C.US_RESIDENT_STANDARD_DEDUCTION_SINGLE - us_se_tax * 0.5)
        us_ordinary_tax_val = us_ordinary_tax(us_ordinary_taxable)
        us_div_rate = us_long_term_capital_gains_rate(us_taxable_income)
        us_div_tax = round(qualified_div * us_div_rate, 2)
        if qualified_div > 0:
            us_notes.append(f"合格股息（持有 >60 天）按 LTCG {us_div_rate*100:.0f}%")
        if nonqualified_div > 0:
            us_notes.append("非合格股息（持有 ≤60 天）并入普通所得计税")
        us_cg_rate = us_long_term_capital_gains_rate(us_taxable_income)
        us_cg_tax = round((lt_gain + cg_cn) * us_cg_rate, 2)  # 长期按 LTCG；短期已并入普通所得
        us_total_tax = round(us_ordinary_tax_val + us_div_tax + us_cg_tax + us_se_tax, 2)
    else:
        # 非居民外国人（NRA）：仅美国来源
        us_div_tax = us_nra_dividend_tax(div_us, True)        # 协定 10%
        us_cg_tax = us_nra_capital_gain_tax(us_cg_total, days_cur)  # <183 天免税
        cb_service = cross_border_service_taxability(bool(inc.get("us_has_fixed_base")), days_cur)
        us_service_tax = us_ordinary_tax(svc_us) if cb_service.taxable_in_us else 0.0
        cb_royalty = cross_border_royalty_treatment(bool(inc.get("us_royalty_connected")))
        us_royalty_tax = us_royalty_withholding_tax(roy_us, True) if cb_royalty.treatment == "withholding" else us_ordinary_tax(roy_us)
        us_total_tax = round(us_div_tax + us_cg_tax + us_service_tax + us_royalty_tax, 2)

    # ================= 境外税收抵免（双向，示例口径） =================
    ftc_cn = None
    ftc_us = None
    cn_total_income = cn_comp_cn + cn_comp_us + div_cn + div_us + cg_cn + us_cg_total
    if cn_res.is_resident and cn_res.six_year_rule_triggered and cn_total_income > 0:
        cn_foreign = _comp(sal_us, svc_us, roy_us) + div_us + us_cg_total
        ftc_cn = foreign_tax_credit_limit(cn_foreign, cn_total_tax, cn_total_income)
    if us_res.is_resident and us_ordinary_gross + div_cn + div_us + cg_cn + us_cg_total > 0:
        us_foreign = sal_cn + svc_cn + roy_cn + div_cn + cg_cn
        us_total_income = us_ordinary_gross + div_cn + div_us + cg_cn + us_cg_total
        ftc_us = foreign_tax_credit_limit(us_foreign, us_total_tax, us_total_income)

    # ================= 综合税负（境外抵免后的一种分配展示） =================
    # 用户可输入实时汇率；默认 7.0 仅为近似值（未来可接实时汇率 API）
    fx_rate = _f(inc.get("fx_rate"), 7.0)
    FX = max(fx_rate, 0.0001)  # 避免除零
    cn_tax_usd = cn_total_tax / FX
    us_tax_usd = us_total_tax
    if cn_tax_usd >= us_tax_usd:
        combined = {
            "fx": FX,
            "higher_country": "china", "higher_tax_usd": round(cn_tax_usd, 2),
            "lower_country": "us", "lower_tax_usd": round(us_tax_usd, 2),
            "residue_usd": round(cn_tax_usd - us_tax_usd, 2),
            "total_usd": round(cn_tax_usd, 2),
        }
    else:
        combined = {
            "fx": FX,
            "higher_country": "us", "higher_tax_usd": round(us_tax_usd, 2),
            "lower_country": "china", "lower_tax_usd": round(cn_tax_usd, 2),
            "residue_usd": round(us_tax_usd - cn_tax_usd, 2),
            "total_usd": round(us_tax_usd, 2),
        }

    return jsonify({
        "china": {
            "is_resident": cn_res.is_resident,
            "reason": cn_res.reason,
            "reason_en": cn_res.reason_en,
            "is_domiciled": cn_res.is_domiciled,
            "days_cn": cn_res.days_cn,
            "six_year_rule_triggered": cn_res.six_year_rule_triggered,
            "ninety_day_exemption": cn_res.ninety_day_exemption,
            "citations": cn_res.citations,
        },
        "us": {
            "is_resident": us_res.is_resident,
            "reason": us_res.reason,
            "reason_en": us_res.reason_en,
            "substantial_presence_met": us_res.substantial_presence_met,
            "weighted_days": us_res.weighted_days,
            "countable_days": {"current": days_cur, "prev1": days_p1, "prev2": days_p2},
            "exclusions": exclusions,
            "exempt_type": us_exempt_type,
            "citations": us_res.citations,
        },
        "tiebreak": (
            {
                "status": tb_result.status,
                "reason": tb_result.reason,
                "reason_en": tb_result.reason_en,
                "citation": tb_result.citation,
            }
            if tb_result else None
        ),
        "tax": {
            "china": {
                "comprehensive_taxable": cn_taxable,
                "comprehensive_tax": cn_comprehensive_tax,
                "comprehensive_cite": "个税法第3条、第6条",
                "dividend_tax": cn_div_tax,
                "dividend_cite": "财税〔2015〕101号（A股差别化）；境外股息 20%（个税法第3条）",
                "capital_gain_tax": cn_cg_tax,
                "capital_gain_cite": "财税字〔1998〕61号（A股暂免）；境外转让 20%",
                "total_tax": cn_total_tax,
            },
            "us": {
                "ordinary_tax": us_ordinary_tax_val,
                "ordinary_cite": "IRC §1（10%–37%），标准扣除 $16,100",
                "dividend_tax": us_div_tax,
                "capital_gain_tax": us_cg_tax,
                "se_tax": us_se_tax,
                "service_tax": us_service_tax,
                "royalty_tax": us_royalty_tax,
                "total_tax": us_total_tax,
                "notes": us_notes,
            },
            "ftc": {
                "cn_credit_limit": ftc_cn,
                "us_credit_limit": ftc_us,
                "note": "境外抵免限额 = 境外所得 ×（本国总税额/总收入）；中美币种需折算后精确计算",
                "combined": combined,
            },
        },
        "cross_border": {
            "service": (
                {
                    "taxable_in_us": cb_service.taxable_in_us,
                    "reason": cb_service.reason,
                    "reason_en": cb_service.reason_en,
                    "citation": cb_service.citation,
                    "tax": us_service_tax,
                }
                if cb_service else None
            ),
            "royalty": (
                {
                    "treatment": cb_royalty.treatment,
                    "rate": cb_royalty.rate,
                    "reason": cb_royalty.reason,
                    "reason_en": cb_royalty.reason_en,
                    "citation": cb_royalty.citation,
                    "tax": us_royalty_tax,
                }
                if cb_royalty else None
            ),
        },
        "obligations": filing_obligations(cn_res.is_resident, us_res.is_resident, is_exempt_individual=exclusions["exempt"] > 0),
        "information_returns": information_returns(us_res.is_resident),
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    try:
        from waitress import serve  # 生产级纯 Python WSGI（可选依赖）

        serve(app, host="0.0.0.0", port=port)
    except ImportError:
        app.run(host="0.0.0.0", port=port, debug=False)
