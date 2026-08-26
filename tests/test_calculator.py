"""税负测算单元测试。"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tax_engine.calculator import (
    progressive_tax,
    resident_comprehensive_taxable,
    china_resident_comprehensive_tax,
    china_nonresident_monthly_tax,
    china_dividend_tax,
    china_dividend_tax_bucketed,
    china_a_share_capital_gain_tax,
    us_nra_dividend_tax,
    us_nra_capital_gain_tax,
    us_resident_dividend_tax,
    foreign_tax_credit_limit,
)
from tax_engine import constants as C


def test_comprehensive_brackets():
    # 36000 -> 3% -> 1080
    assert china_resident_comprehensive_tax(36000) == 1080.0
    # 100000 -> 10% 档 -> 100000*0.10 - 2520 = 7480
    assert china_resident_comprehensive_tax(100000) == 7480.0
    # 200000 -> 20% 档 -> 200000*0.20 - 16920 = 23080
    assert china_resident_comprehensive_tax(200000) == 23080.0
    # 500000 -> 30% 档 -> 500000*0.30 - 52920 = 97080
    assert china_resident_comprehensive_tax(500000) == 97080.0


def test_comprehensive_zero_and_negative():
    assert china_resident_comprehensive_tax(0) == 0.0
    assert china_resident_comprehensive_tax(-100) == 0.0


def test_nonresident_monthly():
    # 月应税 4000 -> 10% 档 -> 4000*0.10 - 210 = 190
    assert china_nonresident_monthly_tax(4000) == 190.0


def test_resident_taxable_after_deductions():
    # 200000 - 60000 - 10000(专项) - 12000(附加) = 118000
    assert resident_comprehensive_taxable(200000, 10000, 12000) == 118000.0
    # 不足 6 万 -> 0
    assert resident_comprehensive_taxable(50000) == 0.0


def test_dividend_a_share_diff_rate():
    assert china_dividend_tax(10000, True, holding_months=0.5) == 2000.0   # ≤1 月 20%
    assert china_dividend_tax(10000, True, holding_months=1) == 2000.0     # 含 1 月 20%
    assert china_dividend_tax(10000, True, holding_months=6) == 1000.0     # 10%
    assert china_dividend_tax(10000, True, holding_months=12) == 1000.0    # 含 1 年 10%
    assert china_dividend_tax(10000, True, holding_months=13) == 0.0       # 超过 1 年 免征


def test_dividend_non_a_share():
    assert china_dividend_tax(10000, False) == 2000.0  # 20%


def test_dividend_bucketed():
    # ≤1月 20% + (1月,1年] 10% + >1年 0%
    assert china_dividend_tax_bucketed(1000, 2000, 3000) == 400.0  # 200 + 200 + 0
    assert china_dividend_tax_bucketed(0, 0, 5000) == 0.0
    assert china_dividend_tax_bucketed(5000, 0, 0) == 1000.0  # 20%


def test_a_share_capital_gain_exempt():
    assert china_a_share_capital_gain_tax(100000) == 0.0


def test_us_nra_dividend():
    assert us_nra_dividend_tax(100, treaty_applies=True) == 10.0
    assert us_nra_dividend_tax(100, treaty_applies=False) == 30.0


def test_us_nra_capital_gain():
    assert us_nra_capital_gain_tax(1000, us_days_current_year=100) == 0.0   # <183 天免税
    assert us_nra_capital_gain_tax(1000, us_days_current_year=200) == 300.0  # ≥183 天 30%


def test_us_resident_qualified_dividend():
    # 合格股息按长期资本利得税率：0% / 15% / 20% 三档
    assert us_resident_dividend_tax(1000, 40000, qualified=True) == 0.0
    assert us_resident_dividend_tax(1000, 100000, qualified=True) == 150.0
    assert us_resident_dividend_tax(1000, 600000, qualified=True) == 200.0
    # 非合格股息 → None（并入普通所得，原型外）
    assert us_resident_dividend_tax(1000, 100000, qualified=False) is None


def test_foreign_tax_credit_limit():
    # 境外 100 × (总税 30 / 总收入 300) = 10
    assert foreign_tax_credit_limit(100, 30, 300) == 10.0
    assert foreign_tax_credit_limit(100, 30, 0) == 0.0
