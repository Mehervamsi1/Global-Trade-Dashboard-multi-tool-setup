import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import dash
from . import make_app

# Path setup
DATA_PATH = os.environ.get("TRADE_CSV", os.path.join(os.path.dirname(__file__), "..", "data", "trade_data.csv"))

# -------- Load & Prepare Data --------
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
    for col in ["distance_km","adval_tariff_pct","reporter_gdp_bln","partner_gdp_bln",
                "reporter_pop_m","partner_pop_m","reporter_cpi","partner_cpi",
                "export_value_usd_mln","quantity_tonnes","unit_price_usd_per_tonne"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.dropna(subset=["year","reporter_iso3","partner_iso3","product_code","export_value_usd_mln"], inplace=True)
    return df

def weighted_avg(v, w):
    v = np.asarray(v); w = np.asarray(w)
    return np.average(v, weights=w) if w.sum() > 0 else np.nan

def prep_dimensions(df):
    return sorted(df["year"].unique()), sorted(df["reporter_iso3"].unique()), sorted(df["partner_iso3"].unique()), sorted(df["product_code"].unique())

# -------- Plotly Figure Styling --------
def modernize_fig(fig, title=None):
    fig.update_layout(
        template="plotly_white",
        font=dict(family="Poppins, sans-serif", size=14),
        title_font=dict(size=18),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        margin=dict(t=50, b=30, l=30, r=30),
    )
    if title:
        fig.update_layout(title=title)
    return fig

# -------- App Factory --------
def make_app(df):
    years, reporters, partners, products = prep_dimensions(df)

    external_stylesheets = ["https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css"]
    app = Dash(__name__, external_stylesheets=external_stylesheets)
    app.title = "Global Trade Dashboard"
    
    server = app.server

    CARD_STYLE = {
        "flex": "1",
        "border": "1px solid #e0e0e0",
        "padding": "15px",
        "borderRadius": "10px",
        "background": "white",
        "boxShadow": "0 2px 5px rgba(0,0,0,0.05)",
        "textAlign": "center"
    }

    # Layout
    app.layout = html.Div([
        html.Div([
            html.H1("🌐 Global Trade Dashboard", style={
                "fontFamily": "Poppins, sans-serif", "textAlign": "center", "color": "#2c3e50", "marginTop": "20px"
            }),
            html.H5("Explore exports by year, region, FTA, and more", style={
                "textAlign": "center", "color": "#7f8c8d", "marginBottom": "30px"
            }),
            html.H6("The data is purely synthetic. The insights derived from it may not reflect real-world scenarios.", style={
                "textAlign": "center", "color": "#7f8c8d", "marginBottom": "20px"
            })
        ], className="container"),

        html.Div([
            html.Div([
                html.Label("Reporter(s)", className="font-weight-bold"),
                dcc.Dropdown(reporters, value=reporters[:1], multi=True, id="dd-reporter"),
            ], className="col-md-3"),

            html.Div([
                html.Label("Partner(s)", className="font-weight-bold"),
                dcc.Dropdown(partners, multi=True, id="dd-partner"),
            ], className="col-md-3"),

            html.Div([
                html.Label("Product(s)", className="font-weight-bold"),
                dcc.Dropdown(products, multi=True, id="dd-product"),
            ], className="col-md-3"),

            html.Div([
                html.Label("FTA only", className="font-weight-bold"),
                dcc.Checklist(options=[{"label": " Active only", "value": 1}], value=[], id="chk-fta"),
            ], className="col-md-2"),
        ], className="row mb-3", style={"margin": "0 15px"}),

        html.Div([
            html.Label("Year Range", className="font-weight-bold"),
            dcc.RangeSlider(min=years[0], max=years[-1], step=1, value=[years[0], years[-1]],
                            marks={int(y): str(y) for y in years[::5]}, id="sl-year")
        ], style={"margin": "20px"}),

        html.Div(id="kpi-row", className="row", style={"margin": "0 15px 20px 15px"}),

        dcc.Tabs([
            dcc.Tab(label="Executive Summary", children=[
                dcc.Graph(id="ts-value"),
                dcc.Graph(id="bar-top-partners"),
                dcc.Graph(id="treemap-product-share"),
            ]),
            dcc.Tab(label="Prices & Tariffs", children=[
                dcc.Graph(id="line-price"),
                dcc.Graph(id="scatter-tariff-price"),
                dcc.Graph(id="area-fta-share"),
            ]),
            dcc.Tab(label="Geography & Lanes", children=[
                dcc.Graph(id="map-partners"),
                dcc.Graph(id="bubble-distance-value"),
            ]),
            dcc.Tab(label="Table (Top N)", children=[
                html.Div([
                    html.Label("Top N", className="font-weight-bold", style={"margin": "10px 0"}),
                    dcc.Slider(5, 50, 5, value=15, id="topn"),
                    dcc.Graph(id="table-topn"),
                ])
            ])
        ])
    ], style={"fontFamily": "'Poppins', sans-serif", "backgroundColor": "#f8f9fa"})

    # -------- Filtering Logic --------
    def filter_df(df, reporters, partners, products, y0, y1, fta_only):
        f = df[(df["year"] >= y0) & (df["year"] <= y1)]
        if reporters: f = f[f["reporter_iso3"].isin(reporters)]
        if partners: f = f[f["partner_iso3"].isin(partners)]
        if products: f = f[f["product_code"].isin(products)]
        if 1 in (fta_only or []): f = f[f["fta_active"] == 1]
        return f

    # -------- KPI Callback --------
    @app.callback(
        Output("kpi-row", "children"),
        Input("dd-reporter", "value"),
        Input("dd-partner", "value"),
        Input("dd-product", "value"),
        Input("sl-year", "value"),
        Input("chk-fta", "value"),
    )
    def kpis(reporters, partners, products, years, fta_only):
        y0, y1 = years
        f = filter_df(df, reporters, partners, products, y0, y1, fta_only)
        val = f["export_value_usd_mln"].sum()
        qty = f["quantity_tonnes"].sum()
        avg_price = weighted_avg(f["unit_price_usd_per_tonne"], f["quantity_tonnes"])
        wtariff = (f["adval_tariff_pct"] * f["export_value_usd_mln"]).sum() / val if val > 0 else np.nan
        fta_val = f.loc[f["fta_active"] == 1, "export_value_usd_mln"].sum()
        fta_share = (fta_val / val) if val > 0 else np.nan
        partners_ct = f["partner_iso3"].nunique()
        products_ct = f["product_code"].nunique()
        cards = [
            html.Div([html.Div("Export Value (USD mln)"), html.H3(f"{val:,.1f}")], style=CARD_STYLE),
            html.Div([html.Div("Quantity (tonnes)"), html.H3(f"{qty:,.0f}")], style=CARD_STYLE),
            html.Div([html.Div("Avg Unit Price"), html.H3(f"{avg_price:,.0f} USD/t")], style=CARD_STYLE),
            html.Div([html.Div("Weighted Tariff"), html.H3(f"{wtariff:,.2f}%")], style=CARD_STYLE),
            html.Div([html.Div("FTA Share"), html.H3(f"{fta_share * 100:,.1f}%")], style=CARD_STYLE),
            html.Div([html.Div("Unique Partners"), html.H3(f"{partners_ct:,}")], style=CARD_STYLE),
            html.Div([html.Div("Unique Products"), html.H3(f"{products_ct:,}")], style=CARD_STYLE),
        ]
        return cards

    # -------- Charts Callback --------
    @app.callback(
        Output("ts-value", "figure"),
        Output("bar-top-partners", "figure"),
        Output("treemap-product-share", "figure"),
        Output("line-price", "figure"),
        Output("scatter-tariff-price", "figure"),
        Output("area-fta-share", "figure"),
        Output("map-partners", "figure"),
        Output("bubble-distance-value", "figure"),
        Output("table-topn", "figure"),
        Input("dd-reporter", "value"),
        Input("dd-partner", "value"),
        Input("dd-product", "value"),
        Input("sl-year", "value"),
        Input("chk-fta", "value"),
        Input("topn", "value"),
    )
    def update_all(reporters, partners, products, years, fta_only, topn):
        y0, y1 = years
        f = filter_df(df, reporters, partners, products, y0, y1, fta_only)
        base_cpi_2020 = df.loc[df["year"] == 2020, "reporter_cpi"].mean()

        g_ts = f.groupby("year", as_index=False).agg(val=("export_value_usd_mln", "sum"), cpi=("reporter_cpi", "mean"))
        g_ts["real_val"] = g_ts["val"] * (base_cpi_2020 / g_ts["cpi"])
        fig_ts = modernize_fig(px.line(g_ts, x="year", y=["val", "real_val"], labels={"value": "USD mln", "variable": "Series"}))

        g_partner = f.groupby("partner_iso3", as_index=False)["export_value_usd_mln"].sum().nlargest(topn, "export_value_usd_mln")
        fig_bar = modernize_fig(px.bar(g_partner, x="partner_iso3", y="export_value_usd_mln"))

        g_prod = f.groupby("product_code", as_index=False)["export_value_usd_mln"].sum()
        fig_tree = modernize_fig(px.treemap(g_prod, path=["product_code"], values="export_value_usd_mln"))

        g_price = f.groupby(["year", "product_code"], as_index=False).apply(
            lambda d: pd.Series({"avg_price": weighted_avg(d["unit_price_usd_per_tonne"], d["quantity_tonnes"])})
        ).reset_index()
        fig_price = modernize_fig(px.line(g_price, x="year", y="avg_price", color="product_code"))

        g_tar = f.groupby("product_code", as_index=False).apply(
            lambda d: pd.Series({
                "wtariff": (d["adval_tariff_pct"] * d["export_value_usd_mln"]).sum() / max(d["export_value_usd_mln"].sum(), 1e-9),
                "avg_price": weighted_avg(d["unit_price_usd_per_tonne"], d["quantity_tonnes"]),
                "val": d["export_value_usd_mln"].sum()
            })
        ).reset_index()
        fig_sc = modernize_fig(px.scatter(g_tar, x="wtariff", y="avg_price", size="val", color="product_code"))

        g_fta = f.groupby("year").apply(lambda d: pd.Series({
            "FTA": d.loc[d["fta_active"] == 1, "export_value_usd_mln"].sum(),
            "Non-FTA": d.loc[d["fta_active"] != 1, "export_value_usd_mln"].sum()
        })).reset_index()
        fig_area = modernize_fig(px.area(g_fta.melt(id_vars="year", var_name="Status", value_name="value"), x="year", y="value", color="Status"))

        g_map = f.groupby("partner_iso3", as_index=False)["export_value_usd_mln"].sum()
        fig_map = px.choropleth(g_map, locations="partner_iso3", locationmode="ISO-3", color="export_value_usd_mln")
        fig_map.update_geos(showcoastlines=True, showcountries=True, projection_type="natural earth")
        fig_map = modernize_fig(fig_map)

        g_dist = f.groupby(["partner_iso3", "product_code"], as_index=False).agg(
            value=("export_value_usd_mln", "sum"), distance=("distance_km", "mean")
        )
        fig_bub = modernize_fig(px.scatter(g_dist, x="distance", y="value", color="product_code", size="value"))

        g_top = f.groupby("partner_iso3", as_index=False).agg(value=("export_value_usd_mln", "sum"), qty=("quantity_tonnes", "sum"))
        g_top["avg_price"] = g_top["value"] * 1e6 / g_top["qty"].replace(0, np.nan)
        g_top = g_top.nlargest(topn, "value")
        fig_table = go.Figure(data=[go.Table(
            header=dict(values=["Partner", "Value (USD mln)", "Quantity (t)", "Avg Price (USD/t)"]),
            cells=dict(values=[g_top["partner_iso3"], g_top["value"].round(1), g_top["qty"].round(0), g_top["avg_price"].round(0)])
        )])
        fig_table.update_layout(title=f"Top {topn} Partners – Table")

        return fig_ts, fig_bar, fig_tree, fig_price, fig_sc, fig_area, fig_map, fig_bub, fig_table

    return app

# -------- Main --------
if __name__ == "__main__":
    if not os.path.exists(DATA_PATH):
        print("CSV file not found. Please place your file at:", DATA_PATH)
    else:
        df = load_data(DATA_PATH)
        app = make_app(df)
        port = int(os.environ.get("PORT", 8050))
        app.run(debug=False, port=port)
