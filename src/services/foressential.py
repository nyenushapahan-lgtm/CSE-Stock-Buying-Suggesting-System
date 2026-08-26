import pandas as pd

df = pd.read_csv('cse_historical_data.csv')

df_mapping = df[['symbol', 'name']].copy()

df_mapping['sector_name'] = 'Unclassified'

mapping_rules = {
    'Banks': ['BANK'],
    'Diversified Financials': ['FINANCE', 'CAPITAL', 'HOLDINGS', 'INVESTMENT', 'LEASING', 'TRUST'],
    'Food, Beverage & Tobacco': ['PLANTATION', 'ESTATE', 'TEA', 'FOOD', 'BEVERAGE', 'AGRI', 'DAIRY', 'GRAIN', 'BAKERY'],
    'Consumer Services': ['HOTEL', 'RESORT', 'TRAVEL', 'SPA', 'LEISURE'],
    'Materials': ['CEMENT', 'ALUMINIUM', 'PLASTIC', 'CHEMICAL', 'PACKAGING', 'CABLE', 'TILE', 'STEEL', 'GLASS'],
    'Capital Goods': ['ENGINEERING', 'CONSTRUCTION', 'MOTORS', 'MACHINERY'],
    'Insurance': ['INSURANCE', 'ASSURANCE', 'TAKAFUL', 'LIFE'],
    'Utilities': ['POWER', 'ENERGY', 'ELEC', 'HYDRO'],
    'Real Estate Management & Development': ['PROPERTY', 'PROPERTIES', 'LAND', 'DEVELOPMENT', 'REALTY', 'ESTATES'],
    'Health Care Equipment & Services': ['HOSPITAL', 'MEDICAL', 'HEALTH', 'CLINIC', 'PHARMA'],
    'Telecommunication Services': ['TELECOM', 'DIALOG', 'MOBITEL'],
    'Consumer Durables & Apparel': ['APPAREL', 'CLOTHING', 'GARMENT', 'FOOTWEAR'],
    'Retailing': ['SUPERMARKET', 'STORES', 'DISTRIBUTORS']
}

for sector, keywords in mapping_rules.items():
    for keyword in keywords:
        mask = df_mapping['name'].str.upper().str.contains(keyword, na=False)
        df_mapping.loc[mask, 'sector_name'] = sector

final_mapping = df_mapping[['symbol', 'sector_name']]
final_mapping.to_csv('my_mapped_symboled.csv',index=False)

