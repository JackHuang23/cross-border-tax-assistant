"""跨境劳务/版税 + 新增计算函数 + 信息申报表测试。"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tax_engine.cross_border import (
    cross_border_service_taxability,
    cross_border_royalty_treatment,
)
from tax_engine.calculator import us_ordinary_tax, us_royalty_withholding_tax
from tax_engine.obligations import information_returns


def test_us_ordinary_tax():
    assert us_ordinary_tax(12400) == 1240.0   # 10%
    assert us_ordinary_tax(50400) == 5800.0   # 1240 + 38000*12%
    assert us_ordinary_tax(100000) == 16712.0  # 5800 + 49600*22%
    assert us_ordinary_tax(0) == 0.0


def test_us_royalty_withholding_tax():
    assert us_royalty_withholding_tax(100, treaty_applies=True) == 10.0
    assert us_royalty_withholding_tax(100, treaty_applies=False) == 30.0


def test_cross_border_service_fixed_base():
    r = cross_border_service_taxability(True, 0)
    assert r.taxable_in_us is True


def test_cross_border_service_over_183_days():
    r = cross_border_service_taxability(False, 200)
    assert r.taxable_in_us is True


def test_cross_border_service_china_only():
    r = cross_border_service_taxability(False, 100)
    assert r.taxable_in_us is False


def test_cross_border_royalty_passive():
    r = cross_border_royalty_treatment(False)
    assert r.treatment == "withholding"
    assert r.rate == 0.10


def test_cross_border_royalty_connected():
    r = cross_border_royalty_treatment(True)
    assert r.treatment == "business_profit"


def test_information_returns_us_resident():
    forms = [o["form"] for o in information_returns(True)]
    assert "Form 1099-DIV" in forms
    assert "Form 1099-B" in forms


def test_information_returns_nra():
    forms = [o["form"] for o in information_returns(False)]
    assert "Form 1042-S" in forms
