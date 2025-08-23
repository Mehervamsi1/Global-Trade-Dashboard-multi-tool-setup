# Global Trade Dashboard (1975–2020)

End-to-end, cross-tool analytics project for 1M+ rows of bilateral trade data.
This repo contains ready-to-run Python dashboards and step-by-step build guides
for Power BI, Tableau, Amazon QuickSight, and Microsoft Fabric.

## Quick start

1) Put your CSV at `data/trade_data.csv` with columns:

year,reporter_iso3,partner_iso3,product_code,distance_km,fta_active,adval_tariff_pct,
reporter_gdp_bln,partner_gdp_bln,reporter_pop_m,partner_pop_m,reporter_cpi,partner_cpi,
export_value_usd_mln,quantity_tonnes,unit_price_usd_per_tonne


2) Python (Plotly Dash app):
   
cd python
pip install -r requirements.txt
python dash_app.py

Open the printed local URL in your browser.

3) Power BI / Tableau / QuickSight / Fabric:
   Follow the guides in their respective folders.

## Business questions answered

- How did **export value**, **quantities**, and **unit prices** evolve 1975–2020?
- Which **partners** and **products** drove growth and margins?
- What is the effect of **FTA activation** and **tariffs** on trade flows?
- Which lanes (distance) and partners are **strategic** vs. **volatile**?
- Where are the **outliers** and possible **data issues**?

## Folder structure

/data -> place your trade_data.csv here
/python -> Dash app + helpers
/powerbi -> DAX measures + model + page designs
/tableau -> Calculated fields + sheet/dashboard blueprint
/quicksight -> SPICE + visuals + calcs + parameters
/fabric -> Lakehouse + Dataflows Gen2 + semantic model + PBI
/sql -> optional SQL star schema build scripts
/docs -> screenshots & notes


## KPIs (all tools implement the same math)

- **Export Value (USD mln)**: sum(export_value_usd_mln)
- **Quantity (tonnes)**: sum(quantity_tonnes)
- **Avg Unit Price (USD/tonne)**: weighted by quantity
- **Weighted Tariff (%)**: value-weighted
- **FTA Share (%)**: export value under fta_active=1 / total
- **Unique Partners / Products**
- **YoY Growth / CAGR** (real and nominal)
- **Real Export Value (2020 USD mln)**: CPI-deflated to 2020
