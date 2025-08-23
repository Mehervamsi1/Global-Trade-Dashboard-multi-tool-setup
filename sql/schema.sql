-- Optional SQL star schema (for a warehouse)

CREATE TABLE dim_date (
  DateKey INT IDENTITY(1,1) PRIMARY KEY,
  [Year] INT NOT NULL
);

CREATE TABLE dim_country (
  CountryKey INT IDENTITY(1,1) PRIMARY KEY,
  iso3 CHAR(3) NOT NULL,
  CountryName VARCHAR(100),
  Region VARCHAR(50)
);

CREATE TABLE dim_product (
  ProductKey INT IDENTITY(1,1) PRIMARY KEY,
  product_code VARCHAR(20),
  ProductGroup VARCHAR(50)
);

CREATE TABLE fact_trade (
  Year INT,
  reporter_iso3 CHAR(3),
  partner_iso3 CHAR(3),
  product_code VARCHAR(20),
  distance_km FLOAT,
  fta_active TINYINT,
  adval_tariff_pct FLOAT,
  reporter_gdp_bln FLOAT,
  partner_gdp_bln FLOAT,
  reporter_pop_m FLOAT,
  partner_pop_m FLOAT,
  reporter_cpi FLOAT,
  partner_cpi FLOAT,
  export_value_usd_mln FLOAT,
  quantity_tonnes FLOAT,
  unit_price_usd_per_tonne FLOAT
);
