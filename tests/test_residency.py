"""身份判定单元测试。"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tax_engine.residency import (
    determine_china_residency,
    determine_us_residency,
    tie_breaker,
    us_countable_days,
    cn_countable_days,
)


def test_cn_domiciled_is_resident():
    r = determine_china_residency(has_domicile=True, full_24h_days_cn=0)
    assert r.is_resident is True
    assert r.is_domiciled is True


def test_cn_no_domicile_183_days_is_resident():
    r = determine_china_residency(False, 183)
    assert r.is_resident is True


def test_cn_no_domicile_182_days_is_nonresident():
    r = determine_china_residency(False, 182)
    assert r.is_resident is False


def test_cn_six_year_rule():
    # 此前连续满 6 年（满183天且无单次离境超30天）→ 全球所得纳税
    r = determine_china_residency(False, 200, consecutive_qualifying_years=6)
    assert r.six_year_rule_triggered is True
    # 连续仅 5 年 → 境外所得仍免税
    r2 = determine_china_residency(False, 200, consecutive_qualifying_years=5)
    assert r2.six_year_rule_triggered is False


def test_cn_90_day_exemption():
    r = determine_china_residency(False, 60)
    assert r.ninety_day_exemption is True


def test_cn_day_counting_only_full_24h():
    assert cn_countable_days(10) == 10
    assert cn_countable_days(-5) == 0


def test_us_citizen_is_resident():
    r = determine_us_residency(True, 0, 0, 0)
    assert r.is_resident is True


def test_us_spt_met():
    # 当年 60 天 + 1/3*300 + 1/6*300 = 60+100+50 = 210 >= 183，当年>=31
    r = determine_us_residency(False, 60, 300, 300)
    assert r.is_resident is True
    assert r.substantial_presence_met is True


def test_us_spt_not_met_below_31_days():
    # 当年 30 天，即使加权够也不满足（必须当年>=31）
    r = determine_us_residency(False, 30, 366, 366)
    assert r.is_resident is False


def test_us_spt_not_met_low_weighted():
    r = determine_us_residency(False, 60, 0, 0)  # 加权仅 60
    assert r.is_resident is False


def test_us_day_counting_exclusions():
    # 总在美 200 天，排除过境(10) + 通勤(5) + 船员(3) = 182
    assert us_countable_days(200, commuter_days=5, transit_under_24h=10, crew_days=3) == 182


def test_tie_breaker_map_consultation():
    # 中美协定第 4 条第 2 款：个人双重居民由主管当局协商（MAP），非机械判定
    r = tie_breaker()
    assert r.status == "dual"
    assert "协商" in r.reason
    assert "第 4 条" in r.citation
