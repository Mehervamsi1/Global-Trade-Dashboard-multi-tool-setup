# Tableau – build guide & calculated fields

## Data
Connect to `data/trade_data.csv`. Set `year` as Number (whole). Ensure `fta_active` is Number (0/1).

## Calculated fields

- **Export Value (USD mln)**: `SUM([export_value_usd_mln])`
- **Quantity (tonnes)**: `SUM([quantity_tonnes])`
- **Avg Unit Price (USD/tonne)**:
  `SUM([unit_price_usd_per_tonne] * [quantity_tonnes]) / SUM([quantity_tonnes])`
- **Weighted Tariff (%)**:
  `SUM([adval_tariff_pct] * [export_value_usd_mln]) / SUM([export_value_usd_mln])`
- **FTA Share (%)**:
  `SUM(IF [fta_active]=1 THEN [export_value_usd_mln] END) / SUM([export_value_usd_mln])`
- **Real Export Value (2020 USD mln)**:
  `AVG([reporter_cpi])` -> create parameter `Base CPI (2020)` (value: avg CPI of 2020)
  `([Export Value (USD mln)] * [Base CPI (2020)] / AVG([reporter_cpi]))`
- **YoY Export Value (%)** (table calc):
  `ZN((SUM([export_value_usd_mln]) - LOOKUP(SUM([export_value_usd_mln]), -1)) / LOOKUP(SUM([export_value_usd_mln]), -1))`
- **Partner Count**: `COUNTD([partner_iso3])`
- **Product Count**: `COUNTD([product_code])`

## Sheets & Dashboards

**Executive Summary**
- KPIs: above calcs on a single sheet styled as big numbers
- Line: Real Export Value by Year
- Bar: Top Partners by Value (filter by Year/Product)
- Treemap: Product Share of Value

**Prices & Policy**
- Line: Avg Unit Price by Year (color Product)
- Scatter: Weighted Tariff vs Avg Unit Price (size = Value)
- Area: FTA vs Non-FTA share over time

**Markets**
- Map: Partner ISO3 (use `Map → Locations → Country/Region` with ISO-3)
- Matrix: Partner x Product (Value, Qty)

Add dashboard actions: filter on map; highlight partners.
