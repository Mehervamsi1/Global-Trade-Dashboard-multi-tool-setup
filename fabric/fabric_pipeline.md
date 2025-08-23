# Microsoft Fabric – Lakehouse + Semantic Model + Power BI

## Pipeline
1) **Dataflow Gen2**: Ingest `trade_data.csv` from Blob/SharePoint/OneLake.
   - Data type casts (whole number for `year`, decimal for numeric fields).
   - Output to **Lakehouse** as Delta table `fact_trade`.

2) **Notebook (PySpark or Pandas)**:
   - Build `dim_date`, `dim_country` (ISO3 → name/region), `dim_product`.
   - Write Delta tables to Lakehouse. Create views.

3) **Semantic Model** (in Fabric):
   - Create model over Lakehouse SQL endpoint. Relationships:
     `dim_date[Year] -> fact_trade[year]` (1:*), etc.
   - Define measures (same DAX as in /powerbi/measures_and_pages.md).

4) **Power BI Report** in Fabric:
   - Build pages per that guide. Enable **Incremental Refresh** on fact_trade by `year`.
   - Add **Deployment Pipeline** (Dev → Test → Prod).

5) **Governance & Performance**
   - Star schema, summarization tables (year×partner×product).
   - Use aggregations for map/treemap; detail pages drill through to transaction rows.
