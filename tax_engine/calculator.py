"""税负测算：综合所得、股息红利、资本利得、境外抵免。"""
from . import constants as C


def progressive_tax(amount: float, brackets, rates, quick) -> float:
    """超额累进：应纳税额 = 应纳税所得额 × 税率 − 速算扣除数。"""
    if amount is None or amount <= 0:
        return 0.0
    for i in range(len(rates)):
        if amount <= brackets[i + 1]:
            return round(amount * rates[i] - quick[i], 2)
    return round(amount * rates[-1] - quick[-1], 2)


def resident_comprehensive_taxable(
    annual_income: float,
    special_deduction: float = 0.0,      # 专项扣除（三险一金等）
    special_additional: float = 0.0,    # 专项附加扣除（子女教育等）
    other_deduction: float = 0.0,       # 依法确定的其他扣除
) -> float:
    """居民综合所得应纳税所得额 = 收入 − 6 万 − 专项扣除 − 专项附加扣除 − 其他。"""
    taxable = (
        (annual_income or 0)
        - C.CN_RESIDENT_BASIC_DEDUCTION
        - (special_deduction or 0)
        - (special_additional or 0)
        - (other_deduction or 0)
    )
    return max(0.0, round(taxable, 2))


def china_resident_comprehensive_tax(annual_taxable_income: float) -> float:
    return progressive_tax(
        annual_taxable_income,
        C.CN_COMPREHENSIVE_BRACKETS,
        C.CN_COMPREHENSIVE_RATES,
        C.CN_COMPREHENSIVE_QUICK,
    )


def china_nonresident_monthly_tax(monthly_taxable_income: float) -> float:
    """非居民工资薪金（按月）：月收入 − 5000 元后按月税率表。"""
    return progressive_tax(
        monthly_taxable_income,
        C.CN_NONRESIDENT_BRACKETS,
        C.CN_NONRESIDENT_RATES,
        C.CN_NONRESIDENT_QUICK,
    )


def china_business_tax(annual_taxable_income: float) -> float:
    return progressive_tax(
        annual_taxable_income,
        C.CN_BUSINESS_BRACKETS,
        C.CN_BUSINESS_RATES,
        C.CN_BUSINESS_QUICK,
    )


def china_dividend_tax(
    dividend_amount: float,
    is_a_share: bool = True,
    holding_months: float = None,
) -> float:
    """股息红利：A 股按持股期差别化（财税〔2015〕101 号），其余 20%。"""
    amount = max(0.0, dividend_amount or 0)
    if not is_a_share:
        return round(amount * C.CN_OTHER_RATE, 2)
    # 财税〔2015〕101 号：≤1 个月（含）→20%；(1 个月, 1 年]（含 1 年）→10%；超过 1 年→0%
    if holding_months is not None and holding_months > 12:
        rate = C.CN_DIVIDEND_DIFF_RATE["gt_1y"]
    elif holding_months is not None and holding_months > 1:
        rate = C.CN_DIVIDEND_DIFF_RATE["1m_12m"]
    else:
        rate = C.CN_DIVIDEND_DIFF_RATE["lte_1m"]
    return round(amount * rate, 2)


def china_dividend_tax_bucketed(lte_1m: float, m_1m_12m: float, gt_1y: float) -> float:
    """A 股股息按持有期分桶计税（财税〔2015〕101 号）：
    ≤1 月 20%；(1 月, 1 年] 10%；超过 1 年 0%。
    逐笔持仓由前端把每笔股息按持有期分到三档，此处分别计税后求和。
    """
    return round(
        (lte_1m or 0) * C.CN_DIVIDEND_DIFF_RATE["lte_1m"]
        + (m_1m_12m or 0) * C.CN_DIVIDEND_DIFF_RATE["1m_12m"]
        + (gt_1y or 0) * C.CN_DIVIDEND_DIFF_RATE["gt_1y"],
        2,
    )


def china_a_share_capital_gain_tax(gain_amount: float) -> float:
    """转让沪深上市公司股票所得暂免个税（财税字〔1998〕61 号）。"""
    return 0.0


def us_nra_dividend_tax(dividend_amount: float, treaty_applies: bool = True) -> float:
    """美国 NRA 股息：预提 30%，适用中美税收协定第 9 条降至 10%。"""
    rate = C.US_NRA_DIVIDEND_TREATY_RATE if treaty_applies else C.US_NRA_DIVIDEND_RATE
    return round((dividend_amount or 0) * rate, 2)


def us_nra_capital_gain_tax(gain_amount: float, us_days_current_year: int = 0) -> float:
    """美国 NRA 资本利得：当年在美 <183 天免税；≥183 天按 30% 固定税率。"""
    if int(us_days_current_year or 0) < C.US_NRA_CG_EXEMPT_DAYS:
        return 0.0
    return round((gain_amount or 0) * C.US_NRA_CAPITAL_GAIN_RATE, 2)


def us_long_term_capital_gains_rate(taxable_income: float) -> float:
    """美国长期资本利得/合格股息税率（单身，2025 口径）：0% / 15% / 20%。"""
    income = taxable_income or 0
    if income <= C.US_LTCG_BRACKETS[1]:
        return C.US_LTCG_RATES[0]
    if income <= C.US_LTCG_BRACKETS[2]:
        return C.US_LTCG_RATES[1]
    return C.US_LTCG_RATES[2]


def us_resident_dividend_tax(dividend_amount: float, taxable_income: float, qualified: bool = True):
    """美国居民股息：
    - 合格股息（持有 >60 天）→ 长期资本利得税率（0/15/20%），取其较小者
    - 非合格股息 → 并入普通所得按累进税率（原型外，返回 None）
    """
    if not qualified:
        return None
    rate = us_long_term_capital_gains_rate(taxable_income)
    return round((dividend_amount or 0) * rate, 2)


def foreign_tax_credit_limit(foreign_income: float, total_tax: float, total_income: float) -> float:
    """境外抵免限额 = 境外所得 ×（总税额 / 总收入）（实施条例第 21 条口径）。"""
    if (total_income or 0) <= 0:
        return 0.0
    return round((foreign_income or 0) * ((total_tax or 0) / total_income), 2)


def us_progressive_tax(income: float, brackets, rates) -> float:
    """美国累进税：分段求和（不同于中国的「×税率−速算扣除数」公式）。"""
    if income is None or income <= 0:
        return 0.0
    tax = 0.0
    for i in range(len(rates)):
        lower = brackets[i]
        upper = brackets[i + 1] if i + 1 < len(brackets) else float("inf")
        if income <= lower:
            break
        tax += (min(income, upper) - lower) * rates[i]
    return round(tax, 2)


def us_ordinary_tax(taxable_income: float) -> float:
    """美国普通所得税（2026 单身，10%–37%）。"""
    return us_progressive_tax(taxable_income, C.US_ORDINARY_BRACKETS, C.US_ORDINARY_RATES)


def us_royalty_withholding_tax(royalty_amount: float, treaty_applies: bool = True) -> float:
    """美国来源版税预提：30%，中美税收协定第 11 条降至 10%。"""
    rate = C.US_NRA_DIVIDEND_TREATY_RATE if treaty_applies else C.US_NRA_DIVIDEND_RATE
    return round((royalty_amount or 0) * rate, 2)
