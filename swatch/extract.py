# -*- coding: utf-8 -*-
"""
Turn one article (title + text) into structured facts about a sanctions-related seizure.
Pure rules - no API, no cost, deterministic. Reuses the place / route / vessel / container readers of the
Seizure Watch template (extract_base.py) and adds sanctions regimes, what was seized, who seized it and the
sanctions-evasion indicators named in the article. Every event keeps its link for analyst verification.
"""
import re
from . import lexicon as L
from . import sanctions_geo  # noqa: F401  (adds North Korea, DR Congo, oil terminals, straits ... before places are read)
from . import extract_base as B
from . import sanctions as S

_CURRENCY_USD = {"$": 1.0, "us$": 1.0, "usd": 1.0, "dollars": 1.0, "dollar": 1.0, "euros": 1.08, "euro": 1.08, "€": 1.08, "eur": 1.08,
                 "pounds": 1.27, "pound": 1.27, "£": 1.27, "gbp": 1.27}
_VAL_MULT = {"million": 1e6, "m": 1e6, "mn": 1e6, "billion": 1e9, "bn": 1e9, "b": 1e9, "thousand": 1e3, "k": 1e3}
_VAL_A = re.compile(r"(us\$|\$|usd|€|eur|£|gbp)\s?" + B.NUM + r"\s?(million|billion|thousand|mn|bn|m|b|k)?(?![a-z])")
_VAL_B = re.compile(B.NUM + r"\s?(million|billion|thousand|mn|bn)?\s?(dollars?|euros?|pounds?|usd|eur|gbp)\b")
_BARREL = re.compile(B.NUM + B.MULT + r"[\s-]*(?:of\s+)?(?:[a-z]+\s+){0,2}?(barrels?|bbls?|barriles|barils)(?![a-z])")
_IMO = re.compile(r"\bimo\s*(?:number|no\.?|#|:)?\s*:?\s*(\d{7})\b", re.I)
_FLAG = [re.compile(r"([a-z][a-z' .-]{2,28}?)[- ]flagged"), re.compile(r"flag(?:ged)?\s+(?:(?:of|in|to|under|from)\s+)?(?:the\s+)?([a-z][a-z' .-]{2,28})"),
         re.compile(r"flying\s+(?:the\s+)?(?:flag\s+of\s+)?(?:the\s+)?([a-z][a-z' .-]{2,28})\s+flag"), re.compile(r"under\s+(?:the\s+)?([a-z][a-z' .-]{2,22})\s+flag"), re.compile(r"(?<![a-z])([a-z][a-z' -]{2,22}?)\s+flag\b(?!\s+(?:of|state))")]
_FLAG_FIX = {"panama": "Panama", "panamanian": "Panama", "liberia": "Liberia", "liberian": "Liberia", "gabon": "Gabon", "gabonese": "Gabon",
             "comoros": "Comoros", "comorian": "Comoros", "cameroon": "Cameroon", "cameroonian": "Cameroon", "palau": "Palau", "palauan": "Palau",
             "sierra leone": "Sierra Leone", "sierra leonean": "Sierra Leone", "togo": "Togo", "togolese": "Togo", "barbados": "Barbados",
             "marshall islands": "Marshall Islands", "malta": "Malta", "maltese": "Malta", "cook islands": "Cook Islands", "tanzania": "Tanzania",
             "tanzanian": "Tanzania", "russian": "Russia", "russia": "Russia", "iranian": "Iran", "iran": "Iran", "hong kong": "Hong Kong",
             "chinese": "China", "china": "China", "greek": "Greece", "greece": "Greece", "turkish": "Turkey", "cypriot": "Cyprus", "cyprus": "Cyprus",
             "bahamas": "Bahamas", "bahamian": "Bahamas", "saint kitts and nevis": "Saint Kitts and Nevis", "st kitts": "Saint Kitts and Nevis",
             "djibouti": "Djibouti", "djiboutian": "Djibouti", "guinea-bissau": "Guinea-Bissau", "eswatini": "Eswatini", "benin": "Benin", "beninese": "Benin",
             "sao tome": "Sao Tome and Principe", "mongolia": "Mongolia", "mongolian": "Mongolia", "north korean": "North Korea", "venezuelan": "Venezuela",
             "singapore": "Singapore", "indian": "India", "emirati": "United Arab Emirates", "belize": "Belize", "belizean": "Belize", "guyana": "Guyana", "guyanese": "Guyana"}


def _value_usd(t):
    best = 0.0
    for rxp, cur_g, num_g, mult_g in ((_VAL_A, 1, 2, 3), (_VAL_B, 3, 1, 2)):
        for m in rxp.finditer(t):
            try:
                v = B.parse_num(m.group(num_g), True)
            except Exception:
                continue
            cur = _CURRENCY_USD.get(m.group(cur_g).lower().strip(), 1.0)
            mult = _VAL_MULT.get((m.group(mult_g) or "").lower(), 1.0)
            val = v * mult * cur
            if mult == 1.0 and val < 1000:                  # "$5" or "EUR 20" is a price, not the value of a seizure
                continue
            if val <= 5e11:
                best = max(best, val)
    return best or None


def _barrels(t):
    best = 0.0
    for m in _BARREL.finditer(t):
        try:
            v = B.parse_num(m.group(1), True) * B._mult(m.group(2))
        except Exception:
            continue
        if 100 <= v <= 5e8:
            best = max(best, v)
    return best or None


def _weight_kg(t):
    best = 0.0
    for m in B.WEIGHT_RX.finditer(t):
        try:
            v = B.parse_num(m.group(1), True) * B._mult(m.group(2)) * B._kg_factor(m.group(3))
        except Exception:
            continue
        if 1 <= v <= 5e8:
            best = max(best, v)
    return best or None


def _units(t):
    best, kind = 0.0, None
    for m in B.UNIT_RX.finditer(t):
        try:
            v = B.parse_num(m.group(1), True) * B._mult(m.group(2))
        except Exception:
            continue
        unit = re.sub(r"\s+", " ", m.group(3)).strip()
        if 2 <= v <= 5e7 and v > best:
            best, kind = v, unit
    return (best or None), kind


def _flag(t):
    for rxp in _FLAG:
        for m in rxp.finditer(t):
            cand = re.sub(r"\s+", " ", m.group(1)).strip(" .-'")
            words = cand.split()
            for n in (3, 2, 1):                       # the last one to three words before "flagged"
                key = " ".join(words[-n:]) if rxp is _FLAG[0] else " ".join(words[:n])
                if key in _FLAG_FIX:
                    return _FLAG_FIX[key]
                if key in L.COUNTRY_ALIAS:
                    return L.COUNTRY_ALIAS[key]
    return None


def _categorise(title_n, t):
    """(category, item, cargo). The seized vessel wins when the headline says a tanker or ship was seized; the goods
    aboard are then the cargo. Otherwise the first item in S.ITEMS (priority order) found in the headline, then the text."""
    lead = title_n + ". " + t[len(title_n) + 2: len(title_n) + 900]
    vessel_seized = bool(S.VESSEL_SEIZED_RX.search(lead))

    def first_item(blob, skip_cat=None):
        for cat, label, pat in S.ITEMS:
            if skip_cat and cat == skip_cat:
                continue
            if pat.search(blob):
                return cat, label
        return None

    goods = first_item(title_n) or first_item(lead) or first_item(t)
    if vessel_seized:
        cargo = None
        g = first_item(title_n) or first_item(t)
        if g:
            cargo = g[1]
        return S.CAT_VESSEL, S.VESSEL_ITEM, cargo
    if goods:
        return goods[0], goods[1], None
    if re.search(r"cargo|shipment|consignment|goods|container|freight|assets", t):
        return S.CAT_OTHER, "Other sanctioned goods", None
    return None, None, None


def _regimes(t):
    scores = {}
    for name, pat in S.REGIMES.items():
        n = len(pat.findall(t))
        if n:
            scores[name] = n
    ranked = sorted(scores.items(), key=lambda x: -x[1])
    top = ranked[0][1] if ranked else 0
    return [n for n, c in ranked[:3] if c >= max(1, 0.4 * top)]


_ACTOR_NAMES = sorted({**{k: v for k, v in sanctions_geo.DEMONYMS.items() if v}, **{k: v for k, v in L.COUNTRY_ALIAS.items() if len(k) >= 4 and k.isascii()}}.items(),
                      key=lambda kv: -len(kv[0]))
_ACTOR_MAP = dict(_ACTOR_NAMES)
_ACTOR_RX = re.compile(r"(?<![a-z.])(" + "|".join(re.escape(k) for k, _ in _ACTOR_NAMES) + r")(?![a-z])")
_ACTOR_GAP_STOP = re.compile(r"\b(?:of|from|in|at|over|off|for|to|by|on|near|into|with|and|as|after|amid|bound|via)\b")


def _actor(title_n):
    """The country that made the seizure, when the headline starts with it: "Estonia detains ...", "German customs seize ...",
    "US forfeits ...". Only a name that comes before the seizure verb with just agency words between counts."""
    verb = S.SEIZURE.search(title_n)
    if not verb:
        return None
    for m in _ACTOR_RX.finditer(title_n[:verb.start()]):
        gap = title_n[m.end():verb.start()]
        if len(gap) <= 45 and not _ACTOR_GAP_STOP.search(gap):
            return _ACTOR_MAP[m.group(1)]
    return None


def _first_key(d, t):
    for k, pat in d.items():
        if pat.search(t):
            return k
    return None


def _all_keys(d, t):
    return [k for k, pat in d.items() if pat.search(t)]


def _transport(t, vessel_seized, in_container):
    if vessel_seized or in_container:
        return "Sea"
    scores = {k: len(p.findall(t)) for k, p in L.TRANSPORT.items()}
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "Unknown"
    return {"Sea - container/cargo": "Sea", "Air": "Air", "Road": "Road", "Rail": "Rail", "Post/express": "Post/express"}.get(best, best.split(" ")[0])


def locate(title, source_country=None):
    return B._route(L.norm(title), source_country)


def extract(title, text="", source_country=None):
    """Return a dict of facts. rec['relevant'] tells whether it is a real sanctions-related seizure report."""
    title_n, text_n = L.norm(title), L.norm(text)
    t = (title_n + ". " + text_n).strip()
    rec = {"relevant": 0}
    if S.EXCLUDE.search(title_n):
        return rec
    head = title_n + ". " + text_n[:1500]
    if not S.SANCTIONS.search(head) or not S.SEIZURE.search(head):
        return rec
    if S.NEGATED_SEIZURE.search(head) or (S.DESIGNATION_TITLE.search(title_n) and not S.SEIZURE.search(title_n)):
        return rec
    category, item, cargo = _categorise(title_n, t)
    if not category:
        return rec
    vessel_seized = category == S.CAT_VESSEL
    route = B._route(t, source_country)
    if not route["seizure_country"]:                      # "Estonia detains tanker ... in the Gulf of Finland": the actor is the country
        known = {route["origin"], route["destination"]} | set((route["transit"] or "").split("|"))
        for m in B._mentions(t):
            if m[2] == "country" and m[4] not in known:
                route["seizure_country"], route["location_conf"] = m[4], "medium"
                break
    actor = _actor(title_n)
    if actor and (not route["seizure_country"] or route["location_conf"] != "high"):
        route["seizure_country"], route["location_conf"] = actor, "actor"      # the seizing state, not necessarily where it happened
    regimes = _regimes(t)
    if not regimes:
        for c in (route["origin"], route["destination"], route["seizure_country"]):
            if c in S.REGIME_OF_COUNTRY:
                regimes = [S.REGIME_OF_COUNTRY[c]]
                break
    raw = (title or "") + ". " + (text or "")
    in_container = 1 if L.CONTAINER.search(B.NON_SHIP_CONTAINER.sub(" ", t)) else 0
    indicators = [k for k, pat in S.INDICATORS.items() if pat.search(t)]
    if "concealment" in indicators and not (S.SANCTIONS.search(title_n) or vessel_seized):
        indicators.remove("concealment")
    kg, barrels, value = _weight_kg(t), _barrels(t), _value_usd(t)
    units, unit_type = _units(t)
    imo = _IMO.search(raw)
    flag = _flag(t)
    vessel = B._vessel(raw) if (vessel_seized or S.VESSEL_RX.search(title_n)) else None
    arrests = B._arrests(t)
    authorities = _all_keys(S.AUTHORITIES, t)
    agency = _first_key(S.AGENCIES, t)
    transport = _transport(t, vessel_seized, in_container)
    rec.update({
        "relevant": 1, "category": category, "item": item, "cargo": cargo,
        "regimes": "|".join(regimes) or None, "authorities": "|".join(authorities) or None, "agency": agency,
        "qty_kg": kg, "qty_barrels": barrels, "qty_units": units, "unit_type": unit_type, "value_usd": value,
        "vessel": vessel, "imo": imo.group(1) if imo else None, "flag": flag,
        "container_numbers": "; ".join(B._containers(raw)) or None,
        "transport": transport, "in_container": in_container, "arrests": arrests,
        "indicators": "|".join(indicators) or None,
        "sanctioned_party": 1 if "sanctioned_party" in indicators else 0, "actor": actor,
    })
    rec.update(route)
    q = []
    if barrels:
        q.append(f"{barrels:,.0f} barrels")
    if kg:
        q.append(f"{kg / 1000:,.1f} t" if kg >= 1000 else f"{kg:,.0f} kg")
    if units:
        q.append(f"{units:,.0f} {unit_type}")
    if value:
        q.append(f"~${value / 1e6:,.1f}m" if value >= 1e5 else f"~${value:,.0f}")
    bits = [item + (f" ({', '.join(q)})" if q else ""), f"cargo: {cargo}" if cargo else None, "/".join(re.split(r" [/(]", r)[0] for r in regimes) or None,
            ("route: " + route["route"]) if route["route"] else None, f"flag: {flag}" if flag else None,
            f"{arrests} arrests" if arrests else None,
            ("signs: " + ", ".join(i.replace("_", " ") for i in indicators if i != "concealment")) if [i for i in indicators if i != "concealment"] else None]
    rec["mo_summary"] = " | ".join(b for b in bits if b)
    rec["completeness"] = sum([bool(item), bool(regimes), bool(route["seizure_country"]), bool(route["origin"] or route["destination"]),
                               bool(vessel or imo), bool(kg or barrels or units or value), bool(agency)])
    return rec
