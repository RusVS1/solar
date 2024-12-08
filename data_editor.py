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

file = '25.02.2023-03.06.2023.csv'

script_dir = os.path.dirname(os.path.abspath(__file__))
file = os.path.join(script_dir, "data/" + file)
#edit(file)
#replace(file)
rad_add(file)