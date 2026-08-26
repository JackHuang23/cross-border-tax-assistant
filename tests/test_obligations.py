"""申报义务与期限测试。"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tax_engine.obligations import filing_obligations


def test_cn_resident_obligations():
    obs = filing_obligations(True, False)
    labels = [o["zh"] for o in obs]
    assert "综合所得汇算清缴" in labels
    assert "境外所得申报" in labels


def test_us_resident_obligations():
    obs = filing_obligations(False, True)
    forms = [o["form"] for o in obs]
    assert "Form 1040" in forms
    assert "FinCEN Form 114" in forms
    assert "Form 8938" in forms
    assert "Form 1116" in forms


def test_nra_obligations():
    obs = filing_obligations(False, False)
    forms = [o["form"] for o in obs]
    assert "Form 1040-NR" in forms
