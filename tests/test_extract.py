import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from swatch import extract


def test_shadow_fleet_tanker():
    r = extract.extract("Estonia detains tanker Kiwala in Gulf of Finland for lack of valid insurance",
                        "The sanctioned tanker flagged Panama was carrying diesel from Ust-Luga.")
    assert r["relevant"] and r["category"] == "Vessel / tanker" and r["seizure_country"] == "Estonia" and r["flag"] == "Panama"


def test_dual_use_route():
    r = extract.extract("German customs seize microchips bound for Russia via Kazakhstan", "Dual-use goods under EU sanctions export controls.")
    assert r["relevant"] and r["destination"] == "Russia" and r["transit"] == "Kazakhstan"


def test_not_relevant():
    assert not extract.extract("Police seize 500 kg of cocaine at port", "Hidden in bananas.")["relevant"]
    assert not extract.extract("US announces new sanctions on Iranian oil network", "No cargo was seized.")["relevant"]
    assert not extract.extract("Club handed disciplinary sanction after football match", "A ban.")["relevant"]
