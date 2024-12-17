import joblib
from sklearn.ensemble import RandomForestRegressor
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime, timedelta
import paramiko

script_dir = os.path.dirname(os.path.abspath(__file__))
rf_model = os.path.join(script_dir, 'rf_model.pkl')
rf_model = joblib.load(rf_model)

test = "data/data.csv"
test = os.path.join(script_dir, test)
data_test = pd.read_csv(test, sep=',', encoding='utf-8', index_col=False)
num_columns = ['N','W1','T','Po','Ff','U','sinα','Ho']
for column in num_columns:
    data_test[column] = data_test[column].astype(str).str.replace(',', '.').astype(float)

data_test['MO'] = data_test['MO'].astype(int)
data_test['DY'] = data_test['DY'].astype(int)

data_test['DayOfYear'] = pd.to_datetime(
    data_test[['YEAR', 'MO', 'DY']].astype(str).agg('-'.join, axis=1), errors='coerce'
).dt.dayofyear.fillna(0).astype(int)

data_test['sin_month'] = np.sin(2 * np.pi * data_test['MO'] / 12)
data_test['cos_month'] = np.cos(2 * np.pi * data_test['MO'] / 12)

data_test['sin_hour'] = np.sin(2 * np.pi * data_test['HR'] / 24)
data_test['cos_hour'] = np.cos(2 * np.pi * data_test['HR'] / 24)
data_test['sin_day_year'] = np.sin(2 * np.pi * data_test['DayOfYear'] / 365)
data_test['cos_day_year'] = np.cos(2 * np.pi * data_test['DayOfYear'] / 365)

features = ['sin_month', 'cos_month', 'sin_hour', 'cos_hour', 'sin_day_year', 'cos_day_year',
            'T', 'Po', 'U', 'Ff', 'sinα', 'Ho', 'N', 'W1']

X_test = data_test[features]

rf_pred = rf_model.predict(X_test)
rf_pred = np.where(rf_pred < 2, 0, rf_pred)

start_time = datetime.strptime("00:00", "%H:%M")
time_intervals = [(start_time + timedelta(hours=i)).strftime("%H:%M") for i in range(len(rf_pred))]

tomorrow_date = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")

result = {
    tomorrow_date: {
        "x": time_intervals,
        "y": rf_pred.tolist()
    }
}

script_dir = os.path.dirname(os.path.abspath(__file__))
password_file = os.path.join(script_dir, "password.txt")
with open(password_file, 'r') as file:
    password = file.read().strip()

sftp_config = {
    "host": "istu.webappz.ru",
    "port": 22,
    "username": "rusvs",
    "password": password,
    "remote_path": "/www/solar/data.json"
}

local_path = os.path.join(script_dir, "data.json")

try:
    transport = paramiko.Transport((sftp_config["host"], sftp_config["port"]))
    transport.connect(username=sftp_config["username"], password=sftp_config["password"])
    sftp = paramiko.SFTPClient.from_transport(transport)

    remote_path = sftp_config["remote_path"]
    sftp.get(remote_path, local_path)

    with open(local_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    data.update(result)

    with open(local_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    sftp.put(local_path, remote_path)

except Exception as e:
    print(f"Произошла ошибка: {e}")
finally:
    if 'sftp' in locals():
        sftp.close()
    if 'transport' in locals():
        transport.close()
