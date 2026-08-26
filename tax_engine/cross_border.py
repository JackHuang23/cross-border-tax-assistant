"""跨境劳务/版税（中美税收协定第 13、14、11 条）。

- 第 13 条（独立个人劳务/自雇）：仅在居住国征税，除非在另一国设有
  「固定基地（fixed base）」或当年在另一国停留超过 183 天。
- 第 11 条（版税）：被动版税 10% 预提；若与另一国常设机构/固定基地
  「有效联系（effectively connected）」，则不适用预提，改按营业利润（第 7 条）或
  独立劳务（第 13 条）征税（第 11 条第 4 款）。
"""
from dataclasses import dataclass
from . import constants as C


@dataclass
class CrossBorderServiceResult:
    taxable_in_us: bool
    reason: str
    citation: str
    reason_en: str = ""


@dataclass
class CrossBorderRoyaltyResult:
    treatment: str      # "withholding"（预提） / "business_profit"（营业利润）
    rate: float         # 预提税率；营业利润时为 0（改按累进）
    reason: str
    citation: str
    reason_en: str = ""


def cross_border_service_taxability(has_fixed_base: bool, us_days: int) -> CrossBorderServiceResult:
    """中美协定第 13 条：中国居民美国来源的独立个人劳务/自雇所得。

    原则上仅在中国征税；若在美国有固定基地，或当年在美停留 >183 天，
    则归属于该基地/该期间的部分可在美国征税（有效联系所得 ECI，按累进税率）。
    """
    if has_fixed_base:
        return CrossBorderServiceResult(
            True,
            "在美国设有固定基地，归属于该基地的所得可在美国征税（按有效联系所得 ECI 累进税率）",
            "中美税收协定第 13 条",
            reason_en="Has a fixed base in the U.S., so income attributable to that base may be taxed in the U.S. (as effectively connected income at graduated rates)",
        )
    if int(us_days or 0) > C.CN_RESIDENT_DAYS:
        return CrossBorderServiceResult(
            True,
            "当年在美停留超过 183 天，该期间在美国取得的所得可在美国征税（ECI 累进税率）",
            "中美税收协定第 13 条",
            reason_en="Present in the U.S. for more than 183 days this year, so income derived in the U.S. during that period may be taxed in the U.S. (ECI at graduated rates)",
        )
    return CrossBorderServiceResult(
        False,
        "无美国固定基地且停留不超过 183 天，该劳务所得仅在中国征税",
        "中美税收协定第 13 条",
        reason_en="No U.S. fixed base and present 183 days or less, so the services income is taxable only in China",
    )


def cross_border_royalty_treatment(effectively_connected: bool) -> CrossBorderRoyaltyResult:
    """中美协定第 11 条：中国居民美国来源的版税。

    - 被动版税（与美常设机构/固定基地无有效联系）→ 10% 预提（第 11 条第 2 款）
    - 有效联系 → 不适用预提，改按营业利润/独立劳务（第 11 条第 4 款）
    """
    if effectively_connected:
        return CrossBorderRoyaltyResult(
            "business_profit",
            0.0,
            "版税与美国常设机构/固定基地有效联系，不适用 10% 预提，改按营业利润（第 7 条）征税",
            "中美税收协定第 11 条第 4 款",
            reason_en="Royalties effectively connected with a U.S. PE / fixed base are not subject to the 10% withholding and are taxed as business profits (Art. 7) instead",
        )
    return CrossBorderRoyaltyResult(
        "withholding",
        C.US_NRA_DIVIDEND_TREATY_RATE,
        "被动版税，按协定第 11 条第 2 款适用 10% 预提税率",
        "中美税收协定第 11 条第 2 款",
        reason_en="Passive royalties are subject to a 10% withholding rate under treaty Art. 11(2)",
    )
