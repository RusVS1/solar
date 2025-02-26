import pandas as pd
import os
import json

def edit(file):
    df = pd.read_csv(file, sep=';', encoding='utf-8', index_col=False) 

    df = df.iloc[::-1].reset_index(drop=True)

    df['Местное время в Иркутске'] = pd.to_datetime(df['Местное время в Иркутске'], format='%d.%m.%Y %H:%M')
    df['YEAR'] = df['Местное время в Иркутске'].dt.year
    df['MO'] = df['Местное время в Иркутске'].dt.month
    df['DY'] = df['Местное время в Иркутске'].dt.day
    df['HR'] = df['Местное время в Иркутске'].dt.hour
    df = df.drop(columns=['Местное время в Иркутске'])
    drop_columns = ['P', 'Pa', 'ff10', 'ff3', 'Tn', 'Tx', 'VV', 'Td', 'E', 'Tg', "E'", 'sss']
    df = df.drop(columns=drop_columns, errors='ignore')
    cols = ['YEAR', 'MO', 'DY', 'HR'] + [col for col in df.columns if col not in ['YEAR', 'MO', 'DY', 'HR']]
    df = df[cols]

    df.to_csv(file, sep=';', index=False, encoding='utf-8')

def replace(file):
    df = pd.read_csv(file, sep=';', encoding='utf-8', index_col=False)
    json_dir = os.path.dirname(os.path.abspath(__file__))
    json_file = os.path.join(json_dir, "unique.json") 
    with open(json_file , 'r', encoding='utf-8') as f:
        replacement_rules = json.load(f)
    for column, replacements in replacement_rules.items():
        if column in df.columns:
            df[column] = df[column].replace(replacements)

    df.to_csv(file, sep=';', index=False, encoding='utf-8')

def rad_add(file):
    rad = "rad.csv"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    rad = os.path.join(script_dir, rad)
    df = pd.read_csv(file, sep=';', encoding='utf-8', index_col=False)
    df2 = pd.read_csv(rad, delimiter=';', encoding='utf-8', index_col=False)
    merged_df = pd.merge(df, df2[['MO', 'DY', 'HR', 'sinα', 'Ho']], on=['MO', 'DY', 'HR'], how='left')

    merged_df.to_csv(file, index=False, sep=';')

def solar_add(file):
    solar = "solar4.csv"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    solar = os.path.join(script_dir, solar)
    df = pd.read_csv(file, sep=';', encoding='utf-8', index_col=False)
    df2 = pd.read_csv(solar, delimiter=';', encoding='utf-8', index_col=False)
    merged_df = pd.merge(df, df2[['YEAR', 'MO', 'DY', 'HR', 'ALLSKY_SFC_SW_DIFF', 'CLRSKY_SFC_SW_DWN', 'ALLSKY_SFC_SW_DNI', 'ALLSKY_SFC_SW_DWN']], on=['YEAR', 'MO', 'DY', 'HR'], how='left')
    merged_df.to_csv(file, index=False, sep=';')

file = 'data/01.01.2009-30.07.2024.csv'

script_dir = os.path.dirname(os.path.abspath(__file__))
file = os.path.join(script_dir, file)
#edit(file)
#replace(file)
#rad_add(file)
solar_add(file)