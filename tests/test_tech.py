"""Keyword rules for the Crypto-mining & AI hardware category (no spaCy needed)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from swatch import sanctions as S, lexicon as L


def item(headline):
    n = L.norm(headline)
    for cat, label, pat in S.ITEMS:
        if pat.search(n):
            return cat, label
    return None, None


def test_mining_machines():
    assert item("Customs seizes Bitmain Antminer bitcoin mining machines bound for Iran under sanctions") == (S.CAT_TECH, "Crypto-mining machines (ASIC / rigs)")
    assert item("Police seize bitcoin mining farm equipment in Russia sanctions case")[0] == S.CAT_TECH


def test_ai_hardware():
    assert item("Container with Nvidia H100 GPUs intercepted en route to Russia")[1] == "AI accelerators / GPUs / AI servers"
    assert item("Servers with A100 AI chips detained, export controls")[0] == S.CAT_TECH


def test_not_tech():
    assert item("Coal miners strike over sanctions")[0] != S.CAT_TECH
    assert item("GPS navigation equipment destined for Iran")[0] != S.CAT_TECH
    assert item("Authorities seize crude oil from sanctioned tanker")[0] != S.CAT_TECH
