import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import dash

DATA_PATH = os.environ.get("TRADE_CSV", os.path.join(os.path.dirname(__file__), "..", "data", "trade_data.csv"))

def load_data(path):
    dtype = {
        "year": "int64",
        "reporter_iso3": "string",
        "partner_iso3": "string",
        "product_code": "string",
        "fta_active": "int64",
    }
    usecols = [
        "year","reporter_iso3","partner_iso3","product_code","distance_km","fta_active","adval_tariff_pct",
        "reporter_gdp_bln","partner_gdp_bln","reporter_pop_m","partner_pop_m","reporter_cpi","partner_cpi",
        "export_value_usd_mln","quantity_tonnes","unit_price_usd_per_tonne"
    ]
    df = pd.read_csv(path, usecols=usecols, dtype=dtype)
    # Clean
    for col in ["distance_km","adval_tariff_pct","reporter_gdp_bln","partner_gdp_bln",
                "reporter_pop_m","partner_pop_m","reporter_cpi","partner_cpi",
                "export_value_usd_mln","quantity_tonnes","unit_price_usd_per_tonne"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.dropna(subset=["year","reporter_iso3","partner_iso3","product_code","export_value_usd_mln"], inplace=True)
    return df

def weighted_avg(v, w):
    v = np.asarray(v); w = np.asarray(w)
    if w.sum() == 0:
        return np.nan
    return np.average(v, weights=w)

def prep_dimensions(df):
    years = sorted(df["year"].unique().tolist())
    reporters = sorted(df["reporter_iso3"].dropna().unique().tolist())
    partners = sorted(df["partner_iso3"].dropna().unique().tolist())
    products = sorted(df["product_code"].dropna().unique().tolist())
    return years, reporters, partners, products

def make_app(df):
    years, reporters, partners, products = prep_dimensions(df)
    app = Dash(__name__)
    app.title = "Global Trade Dashboard"
    server = app.server

    app.layout = html.Div([
        html.H2("Global Trade Dashboard (1975–2020)"),
        html.Div([
            html.Div([
                html.Label("Reporter(s)"),
                dcc.Dropdown(reporters, value=reporters[:1], multi=True, id="dd-reporter"),
            ], style={"width":"20%","display":"inline-block","verticalAlign":"top"}),
            html.Div([
                html.Label("Partner(s)"),
                dcc.Dropdown(partners, multi=True, id="dd-partner"),
            ], style={"width":"20%","display":"inline-block","verticalAlign":"top"}),
            html.Div([
                html.Label("Product(s)"),
                dcc.Dropdown(products, multi=True, id="dd-product"),
            ], style={"width":"20%","display":"inline-block","verticalAlign":"top"}),
            html.Div([
                html.Label("Year range"),
                dcc.RangeSlider(min=years[0], max=years[-1], step=1, value=[years[0], years[-1]],
                                marks={y:str(y) for y in years[::5]}, id="sl-year"),
            ], style={"width":"35%","display":"inline-block","padding":"0 20px","verticalAlign":"top"}),
            html.Div([
                html.Label("FTA only"),
                dcc.Checklist(options=[{"label":"Active only", "value":1}], value=[], id="chk-fta"),
            ], style={"width":"5%","display":"inline-block","verticalAlign":"top"}),
        ], style={"marginBottom":"10px"}),

        # KPI row
        html.Div(id="kpi-row", style={"display":"flex","gap":"12px","marginBottom":"10px"}),

        dcc.Tabs([
            dcc.Tab(label="Executive Summary", children=[
                html.Div([
                    dcc.Graph(id="ts-value"),
                    dcc.Graph(id="bar-top-partners"),
                    dcc.Graph(id="treemap-product-share"),
                ])
            ]),
            dcc.Tab(label="Prices & Tariffs", children=[
                html.Div([
                    dcc.Graph(id="line-price"),
                    dcc.Graph(id="scatter-tariff-price"),
                    dcc.Graph(id="area-fta-share"),
                ])
            ]),
            dcc.Tab(label="Geography & Lanes", children=[
                html.Div([
                    dcc.Graph(id="map-partners"),
                    dcc.Graph(id="bubble-distance-value"),
                ])
            ]),
            dcc.Tab(label="Table (Top N)", children=[
                html.Div([
                    dcc.Slider(5, 50, 5, value=15, id="topn"),
                    dcc.Graph(id="table-topn"),
                ])
            ])
        ])
    ], style={"fontFamily":"Arial, Helvetica, sans-serif","padding":"10px"})

    def filter_df(df, reporters, partners, products, y0, y1, fta_only):
        f = df[(df["year"]>=y0) & (df["year"]<=y1)]
        if reporters:
            f = f[f["reporter_iso3"].isin(reporters)]
        if partners:
            f = f[f["partner_iso3"].isin(partners)]
        if products:
            f = f[f["product_code"].isin(products)]
        if 1 in (fta_only or []):
            f = f[f["fta_active"]==1]
        return f

    @app.callback(
        Output("kpi-row","children"),
        Input("dd-reporter","value"),
        Input("dd-partner","value"),
        Input("dd-product","value"),
        Input("sl-year","value"),
        Input("chk-fta","value"),
    )
    def kpis(reporters, partners, products, years, fta_only):
        y0, y1 = years
        f = filter_df(df, reporters, partners, products, y0, y1, fta_only)
        val = f["export_value_usd_mln"].sum()
        qty = f["quantity_tonnes"].sum()
        avg_price = weighted_avg(f["unit_price_usd_per_tonne"], f["quantity_tonnes"])
        wtariff = (f["adval_tariff_pct"] * f["export_value_usd_mln"]).sum() / val if val>0 else np.nan
        fta_val = f.loc[f["fta_active"]==1, "export_value_usd_mln"].sum()
        fta_share = (fta_val/val) if val>0 else np.nan
        partners_ct = f["partner_iso3"].nunique()
        products_ct = f["product_code"].nunique()
        cards = [
            html.Div([html.Div("Export Value (USD mln)"), html.H3(f"{val:,.1f}")], className="card"),
            html.Div([html.Div("Quantity (tonnes)"), html.H3(f"{qty:,.0f}")], className="card"),
            html.Div([html.Div("Avg Unit Price"), html.H3(f"{avg_price:,.0f} USD/t")], className="card"),
            html.Div([html.Div("Weighted Tariff"), html.H3(f"{wtariff:,.2f}%")], className="card"),
            html.Div([html.Div("FTA Share"), html.H3(f"{fta_share*100:,.1f}%")], className="card"),
            html.Div([html.Div("Unique Partners"), html.H3(f"{partners_ct:,}")], className="card"),
            html.Div([html.Div("Unique Products"), html.H3(f"{products_ct:,}")], className="card"),
        ]
        for c in cards:
            c.style = {"flex":"1","border":"1px solid #ddd","padding":"8px","borderRadius":"6px","background":"#fafafa"}
        return cards

    @app.callback(
        Output("ts-value","figure"),
        Output("bar-top-partners","figure"),
        Output("treemap-product-share","figure"),
        Output("line-price","figure"),
        Output("scatter-tariff-price","figure"),
        Output("area-fta-share","figure"),
        Output("map-partners","figure"),
        Output("bubble-distance-value","figure"),
        Output("table-topn","figure"),
        Input("dd-reporter","value"),
        Input("dd-partner","value"),
        Input("dd-product","value"),
        Input("sl-year","value"),
        Input("chk-fta","value"),
        Input("topn","value"),
    )
    def update_all(reporters, partners, products, years, fta_only, topn):
        y0, y1 = years
        f = filter_df(df, reporters, partners, products, y0, y1, fta_only)

        # Time series (real to 2020 using reporter_cpi)
        base_cpi_2020 = df.loc[df["year"]==2020, "reporter_cpi"].mean()
        g_ts = f.groupby("year", as_index=False).agg(
            val=("export_value_usd_mln","sum"),
            cpi=("reporter_cpi","mean")
        )
        g_ts["real_val"] = g_ts["val"] * (base_cpi_2020 / g_ts["cpi"])
        fig_ts = px.line(g_ts, x="year", y=["val","real_val"], labels={"value":"USD mln","variable":"Series"},
                         title="Exports: Nominal vs Real (2020 USD mln)")
        fig_ts.update_layout(legend_title=None)

        # Top partners
        g_partner = f.groupby("partner_iso3", as_index=False)["export_value_usd_mln"].sum().sort_values("export_value_usd_mln", ascending=False).head(topn)
        fig_bar = px.bar(g_partner, x="partner_iso3", y="export_value_usd_mln", title=f"Top {topn} Partners by Export Value")

        # Treemap product
        g_prod = f.groupby("product_code", as_index=False)["export_value_usd_mln"].sum().sort_values("export_value_usd_mln", ascending=False)
        fig_tree = px.treemap(g_prod, path=["product_code"], values="export_value_usd_mln", title="Product Share of Export Value")

        # Price line
        g_price = f.groupby(["year","product_code"], as_index=False).apply(
            lambda d: pd.Series({
                "avg_price": weighted_avg(d["unit_price_usd_per_tonne"], d["quantity_tonnes"])
            })
        ).reset_index(drop=True)
        fig_price = px.line(g_price, x="year", y="avg_price", color="product_code", title="Avg Unit Price by Year (weighted)",
                            labels={"avg_price":"USD/tonne"})

        # Tariff vs price
        g_tar = f.groupby("product_code", as_index=False).apply(
            lambda d: pd.Series({
                "wtariff": (d["adval_tariff_pct"]*d["export_value_usd_mln"]).sum()/max(d["export_value_usd_mln"].sum(),1e-9),
                "avg_price": weighted_avg(d["unit_price_usd_per_tonne"], d["quantity_tonnes"]),
                "val": d["export_value_usd_mln"].sum()
            })
        ).reset_index(drop=True)
        fig_sc = px.scatter(g_tar, x="wtariff", y="avg_price", size="val", color="product_code",
                            labels={"wtariff":"Weighted Tariff (%)","avg_price":"Avg Price (USD/t)"},
                            title="Weighted Tariff vs Avg Price (size = value)")

        # FTA share over time
        g_fta = f.groupby(["year"], as_index=False).apply(
            lambda d: pd.Series({
                "FTA": d.loc[d["fta_active"]==1, "export_value_usd_mln"].sum(),
                "Non-FTA": d.loc[d["fta_active"]!=1, "export_value_usd_mln"].sum()
            })
        ).reset_index(drop=True)
        g_fta = g_fta.melt(id_vars="year", var_name="Status", value_name="value")
        fig_area = px.area(g_fta, x="year", y="value", color="Status", title="FTA vs Non-FTA Export Value")

        # Map partners (ISO3)
        g_map = f.groupby("partner_iso3", as_index=False)["export_value_usd_mln"].sum()
        fig_map = px.choropleth(g_map, locations="partner_iso3", locationmode="ISO-3",
                                color="export_value_usd_mln", title="Export Value by Partner (choropleth)",
                                labels={"export_value_usd_mln":"USD mln"})
        fig_map.update_geos(showcoastlines=True, showcountries=True, projection_type="natural earth")

        # Distance bubble
        g_dist = f.groupby(["partner_iso3","product_code"], as_index=False).agg(
            value=("export_value_usd_mln","sum"),
            distance=("distance_km","mean")
        )
        fig_bub = px.scatter(g_dist, x="distance", y="value", color="product_code",
                             hover_name="partner_iso3", size="value",
                             labels={"distance":"Distance (km)","value":"USD mln"},
                             title="Distance vs Export Value (by product)")

        # Table Top N (partners)
        g_top = f.groupby(["partner_iso3"], as_index=False).agg(
            value=("export_value_usd_mln","sum"),
            qty=("quantity_tonnes","sum")
        )
        g_top["avg_price"] = g_top["value"]*1e6 / g_top["qty"].replace(0, np.nan)
        g_top = g_top.sort_values("value", ascending=False).head(topn)
        fig_table = go.Figure(data=[go.Table(
            header=dict(values=["Partner","Value (USD mln)","Quantity (t)","Avg Price (USD/t)"]),
            cells=dict(values=[g_top["partner_iso3"], g_top["value"].round(1), g_top["qty"].round(0), g_top["avg_price"].round(0)])
        )])
        fig_table.update_layout(title=f"Top {topn} Partners – table")

        return fig_ts, fig_bar, fig_tree, fig_price, fig_sc, fig_area, fig_map, fig_bub, fig_table

    return app

if __name__ == "__main__":
    if not os.path.exists(DATA_PATH):
        print("Place your CSV at:", DATA_PATH)
    df = load_data(DATA_PATH)
    app = make_app(df)
    port = int(os.environ.get("PORT", 8050))
    app.run_server(debug=False, port=port)

