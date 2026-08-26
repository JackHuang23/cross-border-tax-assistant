"""中美税务居民身份判定 + 双重居民 tie-breaker。

天数口径（关键，避免财税原则性错误）：
- 中国：仅「当天停留满 24 小时」计入居住天数（2019 年第 34 号公告）。
- 美国：当天任何时候在境内即算 1 天，但排除 5 类例外
  （加/墨通勤、过境且不足 24 小时、船员、医疗、豁免身份）。
"""
from dataclasses import dataclass, field
from . import constants as C


@dataclass
class ChinaResidency:
    is_resident: bool
    reason: str
    is_domiciled: bool
    days_cn: int
    six_year_rule_triggered: bool     # 无住所居民此前连续满 6 年（满183天且无单次离境超30天）→ 全球所得纳税
    ninety_day_exemption: bool        # 无住所且 ≤90 天 → 境外雇主支付部分免征
    citations: list = field(default_factory=list)
    reason_en: str = ""


@dataclass
class USResidency:
    is_resident: bool
    reason: str
    substantial_presence_met: bool
    weighted_days: float
    citations: list = field(default_factory=list)
    reason_en: str = ""


@dataclass
class TieBreakResult:
    status: str          # "dual" — 事实上的双重居民，需主管当局协商
    reason: str
    citation: str = ""
    reason_en: str = ""


def cn_countable_days(full_24h_days: int) -> int:
    """中国侧：仅「满 24 小时」的天数计入境内居住天数。"""
    return max(0, int(full_24h_days or 0))


def us_countable_days(
    gross_days: int,
    commuter_days: int = 0,
    transit_under_24h: int = 0,
    crew_days: int = 0,
    medical_days: int = 0,
    exempt_days: int = 0,
) -> int:
    """美国侧：任何一天在境内都算 1 天，减去 5 类例外天数。

    注意：IRS 原文中「不足 24 小时」的排除是「且处于过境（两个境外地点之间）」
    这一组合情形（AND，非 OR），此处以 transit_under_24h 单独传入。
    """
    gross = int(gross_days or 0)
    excluded = (
        int(commuter_days or 0)
        + int(transit_under_24h or 0)
        + int(crew_days or 0)
        + int(medical_days or 0)
        + int(exempt_days or 0)
    )
    return max(0, gross - excluded)


def determine_china_residency(
    has_domicile: bool,
    full_24h_days_cn: int,
    consecutive_qualifying_years: int = 0,
) -> ChinaResidency:
    """判定中国税务居民身份。

    - 有住所（户籍/家庭/经济利益习惯性居住）→ 居民个人
    - 无住所但居住累计满 183 天 → 居民个人
    - 无住所且不满 183 天 → 非居民个人

    6 年规则（2019 年第 34 号公告第 1 条）：
    consecutive_qualifying_years 指「此前连续每个年度都满 183 天、且没有任何
    一年单次离境超过 30 天」的连续年度数（从前一年往前数）。连续满 6 年 →
    当年来源于中国境内、境外的所得均须纳税（全球所得纳税）；否则境外所得
    （由境外单位或个人支付）免税。
    """
    is_domiciled = bool(has_domicile)
    days_cn = cn_countable_days(full_24h_days_cn)
    six_year_triggered = (not is_domiciled) and (
        consecutive_qualifying_years >= C.CN_SIX_YEAR_THRESHOLD
    )
    ninety_day_exemption = (not is_domiciled) and (days_cn <= C.CN_90_DAY_RULE)

    if is_domiciled:
        return ChinaResidency(
            True,
            "在中国境内有住所（因户籍、家庭、经济利益关系而习惯性居住），为居民个人",
            True,
            days_cn,
            six_year_triggered,
            ninety_day_exemption,
            ["个税法第 1 条", "实施条例第 2 条"],
            reason_en="Domiciled in China (habitual residence by household, family or economic ties), therefore a resident individual",
        )
    if days_cn >= C.CN_RESIDENT_DAYS:
        return ChinaResidency(
            True,
            "无住所，但一个纳税年度内在中国境内居住累计满 183 天，为居民个人",
            False,
            days_cn,
            six_year_triggered,
            ninety_day_exemption,
            ["个税法第 1 条", "2019 年第 34 号公告"],
            reason_en="Not domiciled, but resided in China for 183 days or more in the tax year, therefore a resident individual",
        )
    return ChinaResidency(
        False,
        "无住所，且居住累计不满 183 天，为非居民个人",
        False,
        days_cn,
        six_year_triggered,
        ninety_day_exemption,
        ["个税法第 1 条", "2019 年第 34 号公告"],
        reason_en="Not domiciled and resided for less than 183 days, therefore a non-resident individual",
    )


def determine_us_residency(
    is_us_citizen_or_green_card: bool,
    days_current: int,
    days_prev1: int,
    days_prev2: int,
) -> USResidency:
    """判定美国税务身份（实质停留测试）。

    - 公民/绿卡 → 居民
    - 当年 ≥31 天 且 (当年 + 1/3 去年 + 1/6 前年) ≥ 183 天 → 居民
    - 否则 → 非居民外国人（NRA）
    """
    if is_us_citizen_or_green_card:
        return USResidency(
            True,
            "美国公民或绿卡持有人，为美国税务居民",
            False,
            0.0,
            ["IRC §7701(b)"],
            reason_en="U.S. citizen or green card holder, therefore a U.S. tax resident",
        )
    cur = int(days_current or 0)
    p1 = int(days_prev1 or 0)
    p2 = int(days_prev2 or 0)
    weighted = cur + p1 * C.US_SPT_WEIGHTS["prev1"] + p2 * C.US_SPT_WEIGHTS["prev2"]
    met = cur >= C.US_SPT_MIN_CURRENT_DAYS and weighted >= C.US_SPT_WEIGHTED_THRESHOLD
    if met:
        return USResidency(
            True,
            "满足实质停留测试（当年在美 ≥31 天 且 加权天数 ≥183 天），为美国税务居民",
            True,
            round(weighted, 2),
            ["IRS Substantial Presence Test", "Pub 519"],
            reason_en="Meets the substantial presence test (≥31 days this year and weighted days ≥183), therefore a U.S. tax resident",
        )
    return USResidency(
        False,
        "不满足实质停留测试，为非居民外国人（NRA）",
        False,
        round(weighted, 2),
        ["IRS Substantial Presence Test", "Pub 519"],
        reason_en="Does not meet the substantial presence test, therefore a nonresident alien (NRA)",
    )


def tie_breaker() -> TieBreakResult:
    """中美税收协定第 4 条第 2 款：个人双重居民由双方主管当局协商（MAP）确定。

    注意：中美协定（1984）并未采用 OECD 范本的机械 tie-breaker
    （永久住所 → 重要利益中心 → 习惯性居所 → 国籍），而是规定由主管当局
    「通过协商」确定。因此，在协商确定前，个人应被视为事实上的双重居民，
    对双方均负纳税义务，需分别向双方税务机关申报，并依协定第 22 条申请
    境外税收抵免/免税，以避免双重征税。
    """
    return TieBreakResult(
        "dual",
        "依据中美税收协定第 4 条第 2 款，个人双重居民身份由双方主管当局协商（MAP）确定，"
        "协定未采用机械判定标准。在协商确定前，应视为事实上的双重居民，对中美双方均负有纳税义务，"
        "应分别向双方税务机关申报，并依协定第 22 条申请境外税收抵免/免税以避免双重征税。",
        "中美税收协定第 4 条第 2 款、第 22 条",
        reason_en="Under US-China treaty Art. 4(2), dual residency of an individual is determined by the competent authorities through consultation (MAP), with no mechanical test. Until determined, the individual is treated as a de facto dual resident, liable in both states, and should file in both states and claim foreign tax credit / exemption under Art. 22.",
    )
