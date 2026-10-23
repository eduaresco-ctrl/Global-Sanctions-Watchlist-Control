# Sanctions Seizure Watch

Free, no-API-key platform (same template as Seizure Watch) that searches open-source news every day for **seizures where sanctions were in place**: sanctioned and shadow-fleet tankers, oil and fuel, dual-use goods and export-control breaches, arms-embargo shipments, luxury goods and assets of sanctioned owners, coal and other restricted commodities. It extracts the facts, draws **maps and routes**, and flags sanctions-evasion signs.

## Quick start
```
pip install -r requirements.txt
python run_daily.py --demo            # offline test with invented data -> docs/
python run_daily.py --days 30         # first real run: 30-day backfill
python run_daily.py                   # daily run (incremental)
```
Outputs in `docs/`: `index.html` (dashboard), `data.js`, `events.csv`, `sanctions_watch.xlsx`.

## Put it online (iPad / web only)
1. Create a new GitHub repository (e.g. `Sanctions-seizure-watch`), make it public, upload all files of this folder (drag and drop, keeping the folders, including `.github/workflows/daily.yaml`).
2. Settings > Pages: branch `main`, folder `/docs`.
3. Actions > daily-sanctions-seizure-watch > Run workflow, set days to 30 for the first run.

## What it shows
- **Overview**: counts, what was seized, map of seizure locations (red = high score there).
- **Maps & Routes**: origin → transit → destination arcs (width = reports, red = High), a ports/places layer and a transit-hubs layer, top routes, hotspots.
- **Vessels**: names, IMO numbers, flags; repeat vessels are the strongest leads.
- **Regimes & Goods**: UN, EU, US, UK programmes (Russia, Iran, DPRK, Syria, Venezuela, Libya, Yemen, Somalia, Sudan, DR Congo, Mali, Haiti, Myanmar, Afghanistan, counter-terrorism, Cuba) against what was seized.
- **Evasion Signs**: AIS off, ship-to-ship transfer, false flag, shell company, third-country re-export, false declaration, no insurance, price cap, sanctioned party named.
- **Alerts**, **Report Library**, **How It Works** (score model in plain words).

## Configure
`config.yaml`: Google News editions and queries, GDELT, official newsrooms, RSS, score caps. Word lists (sanctions cues, goods, regimes, evasion signs, hubs) are in `swatch/sanctions.py`; extra ports, straits and STS areas in `swatch/sanctions_geo.py`.

## Notes and limits
- Rule-based extraction in English, Spanish, French, Portuguese, Dutch, German, Russian, Arabic, Chinese and Turkish. Korean, Persian, Greek, Finnish, Japanese and Ukrainian are not yet read: add their words to `swatch/sanctions.py` first.
- "Seized in" can be the seizing country when the seizure was at sea (shown as "at sea, seized by X").
- Indicators are phrases in articles, never traits of a person or nationality; scores justify a closer look and are not proof. Only extracted facts and links are stored.
- Live collection was not tested in the build sandbox (no news access): run the backfill once and check the counts in `data/last_run.log`.

## Source registry

`data/Global_Sanctions_Source_Registry.xlsx` (research baseline 23 October 2026) lists 451 official sanctions, export-control and enforcement sources for 213 countries and jurisdictions, plus a topic map, a multilingual search lexicon, event field definitions and a collection plan. The dashboard shows it on the **Source Registry** page. To update it, replace the workbook and run `python tools/build_registry.py`. Enforcement and export-control sites from the registry are also searched daily (`official_sites` in `config.yaml`).
