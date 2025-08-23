# Power BI – data model & measures

## Model (Star Schema)
- **FactTrade**: one row per (year, reporter_iso3, partner_iso3, product_code)
- **DimDate**: Date table with Year; relate `DimDate[Year]` -> `FactTrade[year]` (single, to many)
- **DimCountry**: ISO3, Country Name, Region
- **DimProduct**: product_code, Product Group

Prefer Import mode; enable Incremental Refresh partitioned by Year.

## Measures (paste into a Measures table)

Export Value (USD mln) =
SUM ( FactTrade[export_value_usd_mln] )

Quantity (tonnes) =
SUM ( FactTrade[quantity_tonnes] )

Avg Unit Price (USD/tonne) =
DIVIDE (
    SUMX ( FactTrade, FactTrade[unit_price_usd_per_tonne] * FactTrade[quantity_tonnes] ),
    [Quantity (tonnes)]
)

Weighted Tariff (%) =
DIVIDE (
    SUMX ( FactTrade, FactTrade[adval_tariff_pct] * FactTrade[export_value_usd_mln] ),
    [Export Value (USD mln)]
)

FTA Export Value (USD mln) =
CALCULATE ( [Export Value (USD mln)], FactTrade[fta_active] = 1 )

FTA Share (%) =
DIVIDE ( [FTA Export Value (USD mln)], [Export Value (USD mln)] )

Unique Partners =
DISTINCTCOUNT ( FactTrade[partner_iso3] )

Unique Products =
DISTINCTCOUNT ( FactTrade[product_code] )

Base CPI (2020) =
CALCULATE ( AVERAGE ( FactTrade[reporter_cpi] ), DimDate[Year] = 2020 )

Deflator (to 2020) =
DIVIDE ( [Base CPI (2020)], AVERAGE ( FactTrade[reporter_cpi] ) )

Real Export Value (2020 USD mln) =
[Export Value (USD mln)] * [Deflator (to 2020)]

YoY Export Value (USD mln) =
VAR Prev = CALCULATE ( [Export Value (USD mln)], DATEADD ( DimDate[Date], -1, YEAR ) )
RETURN [Export Value (USD mln)] - Prev

YoY Export Value (%) =
VAR Prev = CALCULATE ( [Export Value (USD mln)], DATEADD ( DimDate[Date], -1, YEAR ) )
RETURN DIVIDE ( [Export Value (USD mln)] - Prev, Prev )

CAGR Export Value (%) =
VAR FirstYear = MIN ( DimDate[Year] )
VAR LastYear  = MAX ( DimDate[Year] )
VAR N = LastYear - FirstYear
VAR FirstVal = CALCULATE ( [Export Value (USD mln)], DimDate[Year] = FirstYear )
VAR LastVal  = CALCULATE ( [Export Value (USD mln)], DimDate[Year] = LastYear )
RETURN IF ( N > 0 && FirstVal > 0, ( LastVal / FirstVal ) ^ ( 1 / N ) - 1 )

Tariff-Price Corr =
VAR Corr =
    CORREL (
        SUMMARIZE ( FactTrade, FactTrade[year], "tar", AVERAGE ( FactTrade[adval_tariff_pct] ),
                    "price", [Avg Unit Price (USD/tonne)] ),
        [tar], [price]
    )
RETURN Corr

## Pages / visuals

1) **Executive Summary**
   - KPI cards: Export Value, Quantity, Avg Price, Weighted Tariff, FTA Share, Unique Partners
   - Line: Real Export Value (2020 USD mln) by Year
   - Clustered Bar: Top 10 Partners by Value (selected period)
   - Treemap: Product share of value

2) **Markets & Products**
   - Matrix: Partner x Product (Value, Qty, Avg Price)
   - Map: Partner country (ISO3) with Value bubbles
   - Pareto line: Cumulative share of value by partner

3) **Prices & Tariffs**
   - Line: Avg Unit Price vs. Year (by product group)
   - Scatter: Weighted Tariff vs. Avg Unit Price (size = value)
   - Ribbon: Unit price ranking by product over time

4) **FTAs & Policy**
   - Stacked Area: Value by FTA Active (0/1)
   - Line: FTA Share (%) over time
   - Small multiples: partners with largest FTA deltas

5) **Logistics**
   - Bubble: Distance vs. Value (color by product)
   - Heatmap: Distance band x Product (Avg price)

Slicers on Year, Reporter, Partner, Product, FTA.
