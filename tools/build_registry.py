# -*- coding: utf-8 -*-
"""Convert data/Global_Sanctions_Source_Registry.xlsx into web/registry.js (window.SWREG) for the dashboard.
Run:  python tools/build_registry.py   (after replacing the workbook with a newer version)"""
import json, os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XL = os.path.join(ROOT, "data", "Global_Sanctions_Source_Registry.xlsx")


def sheet(name):
    raw = pd.read_excel(XL, sheet_name=name, header=None)
    hi = next(i for i in range(12) if raw.iloc[i].notna().sum() >= 4)
    df = pd.read_excel(XL, sheet_name=name, header=hi).dropna(how="all")
    return df.astype(object).where(df.notna(), None)


def rows(df, mapping):
    out = []
    for _, r in df.iterrows():
        d = {}
        for short, col in mapping.items():
            v = r.get(col)
            if v is not None:
                v = str(v).strip() if not isinstance(v, (int, float)) else (int(v) if float(v).is_integer() else v)
            d[short] = v
        if any(d.values()):
            out.append(d)
    return out


def main():
    src = rows(sheet("Source registry"), {
        "id": "Source ID", "co": "Country / jurisdiction", "au": "Authority", "nm": "Source / publication", "url": "Website", "ty": "Source type",
        "pr": "Priority", "ve": "Verification", "ly": "Coverage layer", "rb": "Regime basis", "fm": "Published formats", "no": "Scope / access / interpretation notes",
        "tp": "Discovery topics", "rg": "Region", "cl": "Jurisdiction class", "cs": "Connector status", "ru": "Reuse terms", "rd": "Research date"})
    cov = rows(sheet("Country coverage"), {
        "co": "Country / jurisdiction", "au": "Primary authority / entry point", "url": "Primary website", "st": "Coverage status", "n": "Source rows",
        "li": "List-source rows", "bl": "195-country baseline", "rg": "Region", "sr": "Subregion", "sh": "Shared sources / application", "no": "Coverage notes", "un": "UN status", "ids": "Linked source IDs"})
    top = rows(sheet("Topic map"), {
        "th": "Theme", "ju": "Jurisdiction", "au": "Suggested authority", "url": "Official website", "ro": "Role in reporting", "di": "Interpretation distinctions",
        "ev": "Event types", "fi": "Recommended event fields", "ids": "Linked source IDs"})
    lex = rows(sheet("Search lexicon"), {
        "co": "Concept", "en": "English", "es": "Spanish", "fr": "French", "de": "German", "pt": "Portuguese", "ru": "Russian", "ar": "Arabic", "zh": "Simplified Chinese", "no": "Extraction / false-positive notes"})
    fld = rows(sheet("Event fields"), {"gr": "Field group", "f": "Field name", "ty": "Data type", "rq": "Requirement", "de": "Definition and interpretation", "ex": "Illustrative example"})
    plan = rows(sheet("Collection plan"), {"st": "Stage", "fo": "Collection focus", "so": "Sources to prioritize", "wk": "Recommended work"})
    data = {"baseline": "23 October 2026", "sources": src, "countries": cov, "topics": top, "lexicon": lex, "fields": fld, "plan": plan}
    out = os.path.join(ROOT, "web", "registry.js")
    open(out, "w", encoding="utf-8").write("window.SWREG=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";")
    print({k: len(v) for k, v in data.items() if isinstance(v, list)}, os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    main()
