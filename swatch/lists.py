# -*- coding: utf-8 -*-
"""
Official sanctions lists, used to name the sanctioned people, companies and vessels in a report.

Each run downloads the public lists (US OFAC SDN, UN Security Council consolidated list, EU consolidated list),
builds a name index and looks for those names in the headlines of each event. Nothing is guessed: a name is only
shown if it is written on an official list AND appears in the headlines. A list that cannot be downloaded is
skipped with a message; the run never fails because of it.

Single-word names are never matched on their own (too many false hits). Vessels are matched by IMO number
when the report has one, otherwise by a multi-word name.
"""
import csv
import io
import json
import os
import re
import unicodedata
import xml.etree.ElementTree as ET

import requests

UA = {"User-Agent": "Mozilla/5.0 (compatible; SanctionsSeizureWatch/1.0)"}
SOURCES = {
    "OFAC": {"sdn": ["https://www.treasury.gov/ofac/downloads/sdn.csv", "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.CSV"],
             "alt": ["https://www.treasury.gov/ofac/downloads/alt.csv", "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/ALT.CSV"],
             "add": ["https://www.treasury.gov/ofac/downloads/add.csv", "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/ADD.CSV"]},
    "UN": {"xml": ["https://scsanctions.un.org/resources/xml/en/consolidated.xml"]},
    "UK": {"csv": ["https://sanctionslist.fcdo.gov.uk/docs/UK-Sanctions-List.csv", "https://ofsistorage.blob.core.windows.net/publishlive/ConList.csv"]},
    "US": {"csv": ["https://data.trade.gov/downloadable_consolidated_screening_list/v1/consolidated.csv"]},
    "EU": {"csv": ["https://webgate.ec.europa.eu/fsd/fsf/public/files/csvFullSanctionsList_1_1/content?token=dG9rZW4tMjAxNw"]},
}
MAXGRAM = 8
IMO_RX = re.compile(r"\bIMO\s*(?:No\.?|number|#)?\s*:?\s*(\d{7})\b", re.I)


def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def _get(urls, log=print):
    for u in urls:
        try:
            r = requests.get(u, headers=UA, timeout=90)
            if r.status_code == 200 and len(r.content) > 1000:
                return r.content
            log(f"      list download {u[:70]}: HTTP {r.status_code}")
        except Exception as exc:
            log(f"      list download {u[:70]} failed: {type(exc).__name__}")
    return None


def _kind(raw):
    raw = (raw or "").strip().lower()
    if raw in ("individual", "person", "p"):
        return "Individual"
    if raw in ("vessel", "ship"):
        return "Vessel"
    if raw in ("aircraft",):
        return "Aircraft"
    return "Company"


class Index:
    def __init__(self):
        self.names = {}   # tuple(tokens) -> list of records
        self.imo = {}     # imo -> record
        self.count = {}
        self.rows = {}    # (normalised name, list) -> [name, type, list, programme, country]

    def add(self, name, kind, src, prog="", imo=None, country="", primary=False, alias_of=None):
        if "," in name and kind == "Individual":          # OFAC writes "SURNAME, Given names"
            last, _, first = name.partition(",")
            name = first.strip() + " " + last.strip()
        tok = tuple(norm(name).split())
        rec = {"n": name.strip(), "t": kind, "l": src, "p": (prog or "").strip()}
        if primary and rec["n"]:
            k = (norm(name), src)
            if k not in self.rows:
                self.rows[k] = [rec["n"][:90], kind, src, rec["p"][:60], (country or "").strip()[:40], []]
                self.count[src] = self.count.get(src, 0) + 1
        if alias_of and alias_of in self.rows and rec["n"]:
            aka = self.rows[alias_of][5]
            if len(aka) < 8 and rec["n"][:90] not in aka and norm(rec["n"]) != alias_of[0]:
                aka.append(rec["n"][:90])
        if imo:
            self.imo[imo] = rec
        ok = len(tok) >= 2 and len(" ".join(tok)) >= (10 if kind == "Individual" else 8)
        if ok or (kind == "Vessel" and len(tok) >= 2):
            lst = self.names.setdefault(tok, [])
            if not any(r["l"] == src and r["n"] == rec["n"] for r in lst):
                lst.append(rec)


def parse_ofac(sdn_bytes, alt_bytes, idx, add_bytes=None):
    rows = list(csv.reader(io.StringIO(sdn_bytes.decode("utf-8", "replace"))))
    ctry = {}
    if add_bytes:
        for r in csv.reader(io.StringIO(add_bytes.decode("utf-8", "replace"))):
            if len(r) >= 5 and r[0].strip().isdigit() and r[0] not in ctry and r[4].strip() not in ("", "-0-"):
                ctry[r[0]] = r[4].strip()
    ent = {}
    for r in rows:
        if len(r) < 12 or not r[0].strip().isdigit():
            continue
        kind = _kind(r[2] if r[2].strip() != "-0-" else "")
        imo = None
        m = IMO_RX.search(r[11])
        if m:
            imo = m.group(1)
        nm = r[1]
        if "," in nm and kind == "Individual":
            nm = nm.partition(",")[2].strip() + " " + nm.partition(",")[0].strip()
        ent[r[0]] = (kind, r[3], (norm(nm), "OFAC"))
        idx.add(r[1], kind, "OFAC", r[3], imo, ctry.get(r[0], ""), primary=True)
    if alt_bytes:
        for r in csv.reader(io.StringIO(alt_bytes.decode("utf-8", "replace"))):
            if len(r) >= 4 and r[0] in ent and r[3].strip() not in ("", "-0-"):
                idx.add(r[3], ent[r[0]][0], "OFAC", ent[r[0]][1], alias_of=ent[r[0]][2])


def parse_un(xml_bytes, idx):
    root = ET.fromstring(xml_bytes)
    for kind, tag in (("Individual", "INDIVIDUAL"), ("Company", "ENTITY")):
        for el in root.iter(tag):
            prog = (el.findtext("UN_LIST_TYPE") or "").strip()
            if tag == "INDIVIDUAL":
                nm = " ".join(filter(None, (el.findtext(k) for k in ("FIRST_NAME", "SECOND_NAME", "THIRD_NAME"))))
            else:
                nm = el.findtext("FIRST_NAME") or ""
            cty = (el.findtext(".//NATIONALITY/VALUE") or el.findtext(".//INDIVIDUAL_ADDRESS/COUNTRY") or el.findtext(".//ENTITY_ADDRESS/COUNTRY") or "").strip()
            if nm.strip():
                idx.add(nm, kind, "UN", prog, country=cty, primary=True)
            for al in el.iter("INDIVIDUAL_ALIAS" if tag == "INDIVIDUAL" else "ENTITY_ALIAS"):
                a = (al.findtext("ALIAS_NAME") or "").strip()
                if a:
                    idx.add(a, kind, "UN", prog, alias_of=(norm(nm), "UN"))


def parse_eu(csv_bytes, idx):
    txt = csv_bytes.decode("utf-8-sig", "replace")
    seen = {}
    for r in csv.DictReader(io.StringIO(txt), delimiter=";"):
        nm = (r.get("NameAlias_WholeName") or "").strip()
        if not nm:
            continue
        st = (r.get("Entity_SubjectType") or r.get("Entity_SubjectType_ClassificationCode") or "").lower()
        kind = "Individual" if st.startswith("p") else "Company"
        lid = r.get("Entity_LogicalId") or nm
        first = lid not in seen
        if first:
            seen[lid] = (norm(nm), "EU")
        cty = (r.get("Address_CountryDescription") or r.get("Citizenship_CountryDescription") or "").strip()
        idx.add(nm, kind, "EU", r.get("Entity_Regulation_Programme") or "", country=cty, primary=first, alias_of=None if first else seen[lid])


def parse_uk(csv_bytes, idx):
    """UK Sanctions List (new format with a Name column) or the older OFSI ConList (Name 1 ... Name 6)."""
    rows = list(csv.reader(io.StringIO(csv_bytes.decode("utf-8-sig", "replace"))))
    h = next((i for i, r in enumerate(rows[:6]) if any(c.strip().lower() in ("group type", "designation type", "name 6", "name") for c in r)), None)
    if h is None:
        return
    head = [c.strip().lower() for c in rows[h]]
    col = lambda *names: next((head.index(n) for n in names if n in head), None)
    gt, rg, cc = col("group type", "designation type"), col("regime", "regime name"), col("country", "country of birth", "address country")
    seen = {}
    if "name 6" in head:
        ncols = [head.index(f"name {i}") for i in (1, 2, 3, 4, 5, 6) if f"name {i}" in head]
        gid = col("group id")
        for r in rows[h + 1:]:
            if len(r) < len(head):
                continue
            nm = " ".join(r[i].strip() for i in ncols if r[i].strip())
            g = r[gid] if gid is not None else nm
            first = g not in seen
            if first:
                seen[g] = (norm(nm), "UK")
            idx.add(nm, _kind(r[gt] if gt is not None else ""), "UK", r[rg] if rg is not None else "", country=r[cc] if cc is not None else "", primary=first, alias_of=None if first else seen[g])
    else:
        nc, nt, uid = col("name"), col("name type"), col("unique id", "group id")
        if nc is None:
            return
        for r in rows[h + 1:]:
            if len(r) <= nc or not r[nc].strip():
                continue
            prim = nt is None or "primary" in r[nt].lower()
            u = r[uid] if uid is not None and len(r) > uid else r[nc]
            if prim:
                seen[u] = (norm(r[nc]), "UK")
            idx.add(r[nc], _kind(r[gt] if gt is not None else ""), "UK", r[rg] if rg is not None else "", country=r[cc] if cc is not None and len(r) > cc else "", primary=prim, alias_of=None if prim else seen.get(u))


def parse_csl(csv_bytes, idx, iso):
    """US Consolidated Screening List (Commerce, State and Treasury lists). The OFAC SDN part is skipped: it is read from OFAC directly."""
    for r in csv.DictReader(io.StringIO(csv_bytes.decode("utf-8-sig", "replace"))):
        src = (r.get("source") or "").strip()
        if not src or src.lower().startswith("specially designated"):
            continue
        m = re.search(r"\(([^)]+)\)", src)
        lab = "US " + (m.group(1) if m else src[:18])
        kind = _kind(r.get("type"))
        cc = re.search(r"country['\"]\s*:\s*['\"]([A-Z]{2})", r.get("addresses") or "")
        cty = iso.get(cc.group(1), cc.group(1)) if cc else ""
        idx.add(r.get("name") or "", kind, lab, (r.get("programs") or "")[:60], country=cty, primary=True)
        for a in (r.get("alt_names") or "").split(";"):
            if a.strip():
                idx.add(a, kind, lab, r.get("programs") or "", alias_of=(norm(r.get("name") or ""), lab))


def iso_names():
    """ISO2 -> country name, read from the registry file that ships with the project."""
    out = {}
    try:
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "Global_Sanctions_Source_Registry.csv"), encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                if r.get("country_iso2") and r.get("publisher_jurisdiction") and r["country_iso2"] not in out:
                    out[r["country_iso2"]] = r["publisher_jurisdiction"]
    except Exception:
        pass
    return out


def build(log=print):
    idx = Index()
    iso = iso_names()
    for src, urls in SOURCES.items():
        try:
            if src == "OFAC":
                a = _get(urls["sdn"], log)
                if a:
                    parse_ofac(a, _get(urls["alt"], log), idx, _get(urls["add"], log))
            elif src == "UN":
                a = _get(urls["xml"], log)
                if a:
                    parse_un(a, idx)
            elif src == "UK":
                a = _get(urls["csv"], log)
                if a:
                    parse_uk(a, idx)
            elif src == "US":
                a = _get(urls["csv"], log)
                if a:
                    parse_csl(a, idx, iso)
            else:
                a = _get(urls["csv"], log)
                if a:
                    parse_eu(a, idx)
        except Exception as exc:
            log(f"      {src} list could not be read ({type(exc).__name__}: {exc})")
    log("      official lists loaded: " + (", ".join(f"{k} {v:,} names" for k, v in idx.count.items()) or "none"))
    return idx


def find(idx, texts, imo=None):
    """Names on the official lists that appear in the given headlines."""
    found = {}
    if imo and imo in idx.imo:
        r = idx.imo[imo]
        found[(r["n"], r["l"])] = r
    for t in texts:
        tok = norm(t).split()
        for i in range(len(tok)):
            for n in range(min(MAXGRAM, len(tok) - i), 1, -1):
                for r in idx.names.get(tuple(tok[i:i + n]), ()):
                    found.setdefault((r["n"], r["l"]), r)
    merged = {}
    for r in found.values():
        k = norm(r["n"])
        m = merged.setdefault(k, {"n": r["n"], "t": r["t"], "l": [], "p": []})
        if r["l"] not in m["l"]:
            m["l"].append(r["l"])
        if r["p"] and r["p"] not in m["p"]:
            m["p"].append(r["p"])
    return [{"n": m["n"], "t": m["t"], "l": ", ".join(m["l"]), "p": "; ".join(m["p"])[:80]} for m in merged.values()]


def annotate(events, log=print):
    """Add e['listed'] to each event: official-list names found in its headlines."""
    try:
        idx = build(log)
    except Exception as exc:
        log(f"      official lists skipped ({type(exc).__name__}: {exc})")
        return None
    if not idx.count:
        return None
    hits = 0
    for e in events:
        e["listed"] = find(idx, e.get("titles") or [e.get("title_en") or e.get("title") or ""], e.get("imo"))
        hits += bool(e["listed"])
    log(f"      {hits} events name someone or something on an official list")
    return idx


def write_catalog(idx, out_dir, log=print):
    """docs/sanctioned.js: every listed person, company and vessel, for the Sanctions Lists page."""
    import datetime as dt
    if not idx or not idx.rows:
        return
    rows = sorted(idx.rows.values(), key=lambda r: (r[2], r[0].lower()))
    data = {"asof": dt.date.today().isoformat(), "counts": idx.count, "rows": rows}
    with open(os.path.join(out_dir, "sanctioned.js"), "w", encoding="utf-8") as f:
        f.write("window.SANC=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";")
    log(f"      sanctions catalogue written: {len(rows):,} names")
