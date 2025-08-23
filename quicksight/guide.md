# Amazon QuickSight – dataset, SPICE, visuals

## Dataset
- Upload/ingest `data/trade_data.csv` to QuickSight (or S3 + Athena).
- Import to SPICE (1M+ rows OK), schedule refresh daily/weekly.

## Field wells & folders
Create field folders: Value, Quantity, Price, Tariff, Geography, Time, Policy.

## Calculated fields
- `Export Value (USD mln)` = sum({export_value_usd_mln})
- `Quantity (tonnes)` = sum({quantity_tonnes})
- `Avg Unit Price (USD/tonne)` = sum({unit_price_usd_per_tonne} * {quantity_tonnes}) / sum({quantity_tonnes})
- `Weighted Tariff (%)` = sum({adval_tariff_pct} * {export_value_usd_mln}) / sum({export_value_usd_mln})
- `FTA Share (%)` = sum(ifelse({fta_active}=1,{export_value_usd_mln},0)) / sum({export_value_usd_mln})
- `Base CPI (2020)` = parameter (numeric)
- `Real Export Value (2020 USD mln)` = {Export Value (USD mln)} * {Base CPI (2020)} / avg({reporter_cpi})
- `YoY Export Value (%)` = (sum({export_value_usd_mln}) - periodOverPeriod(sum({export_value_usd_mln}), -1, 'YYYY')) / periodOverPeriod(sum({export_value_usd_mln}), -1, 'YYYY')

## Suggested visuals (one analysis, 3 sheets)
1) **Executive**
   - KPI: Export Value, Quantity, Avg Price, Weighted Tariff, FTA Share
   - Line (Real Export Value by Year), controls: Year range, Product, Partner
   - Top N Partners bar (use parameter for N)

2) **Prices & Policy**
   - Scatter (Weighted Tariff vs Avg Price), size by Value, color by Product
   - Area (FTA vs Non-FTA value share over time)

3) **Geography & Lanes**
   - Map (Country ISO): bubble by value
   - Heatmap (Distance bands × Product): Avg price

Use controls: drop-downs (Reporter, Partner, Product), year slider, FTA toggle.
