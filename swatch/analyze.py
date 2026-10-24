# -*- coding: utf-8 -*-
"""Group reports into events, score them for sanctions-evasion indicators, and find corridors, hotspots,
repeat vessels and alerts. All numbers are read from the news reports and are leads to verify, not findings."""
import collections
import datetime as dt
import statistics

from . import sanctions as S

LABEL = {
    "ais_dark": "AIS / tracking switched off or spoofed", "sts_transfer": "Ship-to-ship transfer at sea", "false_flag": "False, fraudulent or changed flag",
    "front_company": "Shell or front company", "third_country": "Re-export / transshipment via a third country", "false_declaration": "False declaration or forged documents",
    "concealment": "Concealment or smuggling", "name_change": "Vessel renamed or ownership changed", "insurance": "No valid insurance",
    "price_cap": "Price-cap breach", "sanctioned_party": "Sanctioned person, company or vessel named", "intel_led": "Intelligence-led find",
}
METHOD = {"ais_dark": 12, "sts_transfer": 10, "false_declaration": 12, "concealment": 6, "name_change": 6}
NETWORK = {"front_company": 12, "third_country": 12, "sanctioned_party": 10, "false_flag": 10, "insurance": 8, "price_cap": 6, "intel_led": 4}
DEFAULT_RISK = {
    "caps": {"method": 30, "network": 30, "route": 20, "scale": 20},
    "bands": {"high": 50, "medium": 25},
    "route_points": {"diversion_hub_transit": 6, "diversion_hub_cap": 12, "sanctioned_end": 8, "stated_transit": 4, "flag_of_concern": 5},
    "scale_value_usd": [[1e7, 12], [1e6, 8], [1e5, 4]],
    "scale_barrels": [[1e6, 10], [2e5, 6], [5e4, 3]],
    "scale_tonnes": [[1000, 8], [100, 4], [10, 2]],
    "vessel_seized_points": 4,
}
EMERGING_DAYS, SPIKE_MIN, SPIKE_Z, MIN_HISTORY = 60, 3, 2.0, 42


def risk_model_description(cfg=None):
    r = _risk(cfg)
    return {
        "dimensions": [
            {"name": "Method", "cap": r["caps"]["method"], "text": "How the goods or ship hid from view: " + ", ".join(f"{LABEL[k].lower()} ({v})" for k, v in METHOD.items()) + "."},
            {"name": "Network", "cap": r["caps"]["network"], "text": "Who and what is behind it: " + ", ".join(f"{LABEL[k].lower()} ({v})" for k, v in NETWORK.items()) + "."},
            {"name": "Route", "cap": r["caps"]["route"], "text": f"Transit through a known diversion hub ({r['route_points']['diversion_hub_transit']} each), an origin or destination that is itself under sanctions ({r['route_points']['sanctioned_end']}), a stated transit ({r['route_points']['stated_transit']}), a flag registry often named in reports on fraudulent flags ({r['route_points']['flag_of_concern']})."},
            {"name": "Scale", "cap": r["caps"]["scale"], "text": "Stated value (over USD 10m: 12; 1m: 8; 100k: 4), barrels (over 1m: 10), tonnes (over 1,000: 8) and a seized vessel itself (4)."},
        ],
        "bands": r["bands"],
        "note": "Each dimension is capped, so one big number cannot decide the level on its own. Indicators are phrases in the article, never traits of a person or nationality; they justify a closer look and are not proof. Hubs are places where diverted goods are often reported, not accusations against a country.",
    }


def _risk(cfg):
    r = dict(DEFAULT_RISK)
    for k, v in ((cfg or {}).get("risk") or {}).items():
        if isinstance(v, dict) and isinstance(r.get(k), dict):
            r[k] = {**r[k], **v}
        else:
            r[k] = v
    return r


def _thr(rules, x):
    for lim, pts in rules:
        if x and x >= lim:
            return pts
    return 0


def score(ev, cfg=None):
    R = _risk(cfg)
    caps = R["caps"]
    ind = [i for i in (ev.get("indicators") or "").split("|") if i]
    reasons = []
    method = min(caps["method"], sum(METHOD.get(i, 0) for i in ind))
    network = min(caps["network"], sum(NETWORK.get(i, 0) for i in ind))
    for i in ind:
        if i in METHOD or i in NETWORK:
            reasons.append(LABEL[i])
    rp = R["route_points"]
    route = 0
    transit = [x for x in (ev.get("transit") or "").split("|") if x]
    hubs = [h for h in transit + [ev.get("destination") or ""] if h in S.DIVERSION_HUBS and h not in (ev.get("seizure_country"),)]
    if hubs:
        route += min(rp["diversion_hub_cap"], rp["diversion_hub_transit"] * len(set(hubs)))
        reasons.append("Via " + ", ".join(sorted(set(hubs))))
    if transit:
        route += rp["stated_transit"]
    if (ev.get("origin") in S.SANCTIONED_JURISDICTIONS) or (ev.get("destination") in S.SANCTIONED_JURISDICTIONS):
        route += rp["sanctioned_end"]
        reasons.append("Origin or destination under a sanctions programme")
    if ev.get("flag") in S.FLAG_OF_CONCERN:
        route += rp["flag_of_concern"]
        reasons.append("Flag registry often named in reports on fraudulent flags: " + ev["flag"])
    route = min(caps["route"], route)
    scale = 0
    scale += _thr(R["scale_value_usd"], ev.get("value_usd"))
    scale += _thr(R["scale_barrels"], ev.get("qty_barrels"))
    scale += _thr(R["scale_tonnes"], (ev.get("qty_kg") or 0) / 1000.0)
    if ev.get("category") == S.CAT_VESSEL:
        scale += R["vessel_seized_points"]
    scale = min(caps["scale"], scale)
    if scale >= 8:
        reasons.append("Large stated value or quantity")
    total = method + network + route + scale
    dims = sum(1 for x in (method, network, route, scale) if x > 0)
    level = "High" if total >= R["bands"]["high"] and dims >= 2 else "Medium" if total >= R["bands"]["medium"] else "Low"
    return {"score": int(total), "level": level, "dims": {"method": method, "network": network, "route": route, "scale": scale},
            "reasons": reasons[:6], "indicator_labels": [LABEL[i] for i in ind if i in LABEL]}


def load_events(conn):
    rows = conn.execute("SELECT * FROM articles WHERE relevant=1 AND event_id IS NOT NULL ORDER BY COALESCE(published, fetched)").fetchall()
    groups = collections.defaultdict(list)
    for r in rows:
        groups[r["event_id"]].append(dict(r))
    events = []
    for eid, arts in groups.items():
        best = max(arts, key=lambda a: (a["completeness"] or 0, -(len(a["title"] or ""))))
        ev = dict(best)
        for k in ("seizure_country", "seizure_place", "origin", "origin_place", "destination", "destination_place", "transit", "vessel", "imo", "flag",
                  "regimes", "authorities", "agency", "cargo", "container_numbers"):
            if not ev.get(k):
                for a in arts:
                    if a.get(k):
                        ev[k] = a[k]
                        break
        for k in ("qty_kg", "qty_barrels", "qty_units", "value_usd"):
            vals = [a[k] for a in arts if a.get(k)]
            ev[k] = max(vals) if vals else None
        inds = []
        for a in arts:
            for i in (a.get("indicators") or "").split("|"):
                if i and i not in inds:
                    inds.append(i)
        ev["indicators"] = "|".join(inds) or None
        ev["date"] = min((a["published"] or a["fetched"] or "")[:10] for a in arts)
        ev["n"] = len(arts)
        ev["outlets"] = "; ".join(sorted({a["source"] for a in arts if a.get("source")}))[:120]
        ev["urls"] = [a["url"] for a in arts][:5]
        ev["titles"] = [t for a in arts for t in (a.get("title_en"), a.get("title")) if t][:12]
        ev["id"] = eid
        events.append(ev)
    events.sort(key=lambda e: e["date"], reverse=True)
    return events


def _trend(n_recent, n_prior, is_new):
    if is_new:
        return "NEW"
    if n_prior == 0:
        return "up" if n_recent else "-"
    ratio = n_recent / n_prior
    return "up" if ratio >= 1.5 else "down" if ratio <= 0.67 else "steady"


def corridor_table(ev, asof, window, history_ok):
    g = collections.defaultdict(list)
    for e in ev:
        o, d = e.get("origin"), e.get("destination")
        if o and d and o != d:
            g[(o, d)].append(e)
        elif o and e.get("seizure_country") and e.get("location_conf") != "actor" and o != e["seizure_country"] and not d:
            g[(o, e["seizure_country"])].append(e)
        elif d and e.get("seizure_country") and e.get("location_conf") != "actor" and d != e["seizure_country"] and not o:
            g[(e["seizure_country"], d)].append(e)
    out = []
    for (o, d), lst in g.items():
        dates = sorted(x["date"] for x in lst)
        recent = [x for x in lst if (asof - dt.date.fromisoformat(x["date"])).days < window]
        prior = [x for x in lst if window <= (asof - dt.date.fromisoformat(x["date"])).days < 2 * window]
        first = dt.date.fromisoformat(dates[0])
        is_new = history_ok and (asof - first).days <= EMERGING_DAYS and len(lst) >= 1
        cats = collections.Counter(x["item"] for x in lst).most_common(2)
        out.append({"origin": o, "destination": d, "events": len(lst), "recent": len(recent), "prior": len(prior), "first_seen": dates[0], "last_seen": dates[-1],
                    "trend": _trend(len(recent), len(prior), is_new), "main_items": "; ".join(c for c, _ in cats),
                    "transit": "; ".join(sorted({t for x in lst for t in (x.get("transit") or "").split("|") if t})),
                    "high": sum(1 for x in lst if x["risk"]["level"] == "High")})
    out.sort(key=lambda c: (-c["events"], -c["recent"]))
    return out


def hotspot_table(ev, asof, window):
    g = collections.defaultdict(list)
    for e in ev:
        key = e.get("seizure_place") or e.get("seizure_country")
        if key:
            g[(key, e.get("seizure_country"))].append(e)
    out = []
    for (place, country), lst in g.items():
        recent = [x for x in lst if (asof - dt.date.fromisoformat(x["date"])).days < window]
        out.append({"place": place, "country": country, "events": len(lst), "recent": len(recent),
                    "main_items": "; ".join(c for c, _ in collections.Counter(x["item"] for x in lst).most_common(2)),
                    "high": sum(1 for x in lst if x["risk"]["level"] == "High")})
    out.sort(key=lambda h: (-h["events"], -h["recent"]))
    return out


def vessel_table(ev):
    g = collections.defaultdict(list)
    for e in ev:
        key = ("IMO " + e["imo"]) if e.get("imo") else (e.get("vessel") or None)
        if key:
            g[key].append(e)
    out = []
    for key, lst in g.items():
        out.append({"vessel": key, "name": next((x["vessel"] for x in lst if x.get("vessel")), None), "flag": next((x["flag"] for x in lst if x.get("flag")), None),
                    "events": len(lst), "first_seen": min(x["date"] for x in lst), "last_seen": max(x["date"] for x in lst),
                    "places": "; ".join(sorted({x.get("seizure_place") or x.get("seizure_country") or "" for x in lst} - {""})),
                    "cargo": "; ".join(sorted({x.get("cargo") or "" for x in lst} - {""})), "regimes": "; ".join(sorted({r for x in lst for r in (x.get("regimes") or "").split("|") if r}))})
    out.sort(key=lambda v: (-v["events"], v["last_seen"]))
    return out


def regime_matrix(ev):
    m = collections.defaultdict(collections.Counter)
    for e in ev:
        for r in (e.get("regimes") or "Unspecified").split("|"):
            m[r][e["category"]] += 1
    return {r: dict(c) for r, c in m.items()}


def build_alerts(ev, corridors, vessels, asof, history_ok):
    alerts = []
    week = [e for e in ev if (asof - dt.date.fromisoformat(e["date"])).days < 7]
    for e in week:
        if e["risk"]["level"] == "High":
            alerts.append({"severity": "HIGH", "type": "High-score event", "title": f"{e['item']} - {e.get('seizure_place') or e.get('seizure_country') or 'location unknown'}",
                           "detail": f"Score {e['risk']['score']}: " + "; ".join(e["risk"]["reasons"][:3]), "urls": e["urls"][:2]})
    for v in vessels:
        if v["events"] >= 2:
            alerts.append({"severity": "HIGH", "type": "Repeat vessel", "title": f"{v['vessel']} appears in {v['events']} separate seizure reports",
                           "detail": f"{v['first_seen']} to {v['last_seen']}; {v['places']}", "urls": []})
    if history_ok:
        for c in corridors:
            if c["trend"] == "NEW" and c["events"] >= 1 and (asof - dt.date.fromisoformat(c["last_seen"])).days <= 14:
                alerts.append({"severity": "MEDIUM", "type": "New corridor", "title": f"{c['origin']} -> {c['destination']} first reported {c['first_seen']}",
                               "detail": c["main_items"], "urls": []})
        weeks = collections.defaultdict(collections.Counter)
        for e in ev:
            for r in (e.get("regimes") or "Unspecified").split("|"):
                weeks[r][(asof - dt.date.fromisoformat(e["date"])).days // 7] += 1
        for r, c in weeks.items():
            hist = [c.get(i, 0) for i in range(1, 9)]
            mean = statistics.mean(hist)
            sd = statistics.pstdev(hist) or 0.5
            if c.get(0, 0) >= SPIKE_MIN and (c[0] - mean) / sd >= SPIKE_Z:
                alerts.append({"severity": "MEDIUM", "type": "Spike", "title": f"{r}: {c[0]} seizure reports in the last 7 days",
                               "detail": f"8-week average {mean:.1f}", "urls": []})
    sts = collections.Counter(e.get("seizure_place") for e in week if "sts_transfer" in (e.get("indicators") or "") and e.get("seizure_place"))
    for place, n in sts.items():
        if n >= 2:
            alerts.append({"severity": "MEDIUM", "type": "Ship-to-ship hotspot", "title": f"{place}: {n} reports mention ship-to-ship transfers this week", "detail": "", "urls": []})
    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    alerts.sort(key=lambda a: order[a["severity"]])
    return alerts


def run(conn, cfg, asof=None):
    ev = load_events(conn)
    if not ev:
        return None
    asof = asof or dt.date.today()
    a = (cfg or {}).get("analysis") or {}
    window = int(a.get("trend_window_days", 30))
    for e in ev:
        e["risk"] = score(e, cfg)
    first = min(dt.date.fromisoformat(e["date"]) for e in ev)
    history_ok = (asof - first).days >= int(a.get("min_history_days", MIN_HISTORY))
    corridors = corridor_table(ev, asof, window, history_ok)
    vessels = vessel_table(ev)
    return {"asof": asof, "events": ev, "corridors": corridors, "hotspots": hotspot_table(ev, asof, window), "vessels": vessels,
            "matrix": regime_matrix(ev), "alerts": build_alerts(ev, corridors, vessels, asof, history_ok), "history_ok": history_ok,
            "model": risk_model_description(cfg), "first_date": first.isoformat()}
