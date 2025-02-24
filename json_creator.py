import pandas as pd
import json
import os

def update_json_with_column_values(json_file, columns, df):
    if os.path.exists(json_file):
        with open(json_file, 'r', encoding='utf-8') as f:
            replacement_rules = json.load(f)
    else:
        replacement_rules = {}

    for column_name in columns:
        if column_name in df.columns:
            unique_values = df[column_name].unique()

            if column_name not in replacement_rules:
                replacement_rules[column_name] = {}
            for value in unique_values:
                if value not in replacement_rules[column_name]:
                    replacement_rules[column_name][value] = 0

    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(replacement_rules, f, ensure_ascii=False, indent=4)


script_dir = os.path.dirname(os.path.abspath(__file__))

file_csv = '01.01.2009-30.07.2024.csv'
file_csv = os.path.join(script_dir, "data/" + file_csv)
file_json = "unique.json"
file_json = os.path.join(script_dir, file_json)

df = pd.read_csv(file_csv, sep=';', encoding='utf-8', index_col=False)
columns_to_process = ["Nh"]
columns_to_process = [col.strip() for col in columns_to_process]

update_json_with_column_values(file_json, columns_to_process, df)
