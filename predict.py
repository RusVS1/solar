import joblib
from sklearn.ensemble import RandomForestRegressor
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime, timedelta
import paramiko

script_dir = os.path.dirname(os.path.abspath(__file__))
rf_model = os.path.join(script_dir, 'model.pkl')
rf_model = joblib.load(rf_model)

test = "data/data.csv"
test = os.path.join(script_dir, test)
data_test = pd.read_csv(test, sep=',', encoding='utf-8', index_col=False)
# num_columns = ['N','W1','T','Po','Ff','U','sinα','Ho']
# for column in num_columns:
#     data_test[column] = data_test[column].astype(str).str.replace(',', '.').astype(float)

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
            'T', 'Po', 'U', 'Ff', 'sinα', 'Ho', 'N', 'W1', 'Nh']

X_test = data_test[features]

rf_pred = rf_model.predict(X_test)
rad_pred = pd.DataFrame(rf_pred, columns=['ALLSKY_SFC_SW_DIFF', 'CLRSKY_SFC_SW_DWN',  'ALLSKY_SFC_SW_DNI', 'ALLSKY_SFC_SW_DWN'])
times = ['YEAR', 'MO', 'DY', 'HR']
df_time = data_test[times]
df = pd.concat([df_time, rad_pred], axis=1)

script_dir = os.path.dirname(os.path.abspath(__file__))
password_file = os.path.join(script_dir, "password.txt")

with open(password_file, 'r') as file:
    password = file.read().strip()

sftp_config = {
    "host": "istu.webappz.ru",
    "port": 22,
    "username": "rusvs",
    "password": password,
    "remote_path": "/www/solar/radiation.json"
}

local_path = os.path.join(script_dir, "radiation.json")

try:
    transport = paramiko.Transport((sftp_config["host"], sftp_config["port"]))
    transport.connect(username=sftp_config["username"], password=sftp_config["password"])
    sftp = paramiko.SFTPClient.from_transport(transport)

    remote_path = sftp_config["remote_path"]
    sftp.get(remote_path, local_path)

    try:
        with open(local_path, "r", encoding="utf-8") as file:
            json_data = json.load(file)
    except FileNotFoundError:
        json_data = {}

    df["date"] = df.apply(lambda row: f"{int(row['YEAR'])}-{int(row['MO']):02d}-{int(row['DY']):02d}", axis=1)
    df["time"] = df["HR"].apply(lambda x: f"{x:02d}:00")

    for _, row in df.iterrows():
        date = row["date"]
        time = row["time"]

        if date not in json_data:
            json_data[date] = {
                "time": [],
                "ALLSKY_SFC_SW_DIFF": [],
                "CLRSKY_SFC_SW_DWN": [],
                "ALLSKY_SFC_SW_DNI": [],
                "ALLSKY_SFC_SW_DWN": []
            }

        if time in json_data[date]["time"]:
            idx = json_data[date]["time"].index(time)
            json_data[date]["ALLSKY_SFC_SW_DIFF"][idx] = row["ALLSKY_SFC_SW_DIFF"]
            json_data[date]["CLRSKY_SFC_SW_DWN"][idx] = row["CLRSKY_SFC_SW_DWN"]
            json_data[date]["ALLSKY_SFC_SW_DNI"][idx] = row["ALLSKY_SFC_SW_DNI"]
            json_data[date]["ALLSKY_SFC_SW_DWN"][idx] = row["ALLSKY_SFC_SW_DWN"]
        else:
            json_data[date]["time"].append(time)
            json_data[date]["ALLSKY_SFC_SW_DIFF"].append(row["ALLSKY_SFC_SW_DIFF"])
            json_data[date]["CLRSKY_SFC_SW_DWN"].append(row["CLRSKY_SFC_SW_DWN"])
            json_data[date]["ALLSKY_SFC_SW_DNI"].append(row["ALLSKY_SFC_SW_DNI"])
            json_data[date]["ALLSKY_SFC_SW_DWN"].append(row["ALLSKY_SFC_SW_DWN"])

        sorted_indices = sorted(range(len(json_data[date]["time"])), key=lambda i: json_data[date]["time"][i])
        json_data[date]["time"] = [json_data[date]["time"][i] for i in sorted_indices]
        json_data[date]["ALLSKY_SFC_SW_DIFF"] = [json_data[date]["ALLSKY_SFC_SW_DIFF"][i] for i in sorted_indices]
        json_data[date]["CLRSKY_SFC_SW_DWN"] = [json_data[date]["CLRSKY_SFC_SW_DWN"][i] for i in sorted_indices]
        json_data[date]["ALLSKY_SFC_SW_DNI"] = [json_data[date]["ALLSKY_SFC_SW_DNI"][i] for i in sorted_indices]
        json_data[date]["ALLSKY_SFC_SW_DWN"] = [json_data[date]["ALLSKY_SFC_SW_DWN"][i] for i in sorted_indices]

    with open(local_path, "w", encoding="utf-8") as file:
        json.dump(json_data, file, ensure_ascii=False, indent=4)

    sftp.put(local_path, remote_path)

    print("JSON успешно обновлен и отправлен на сервер.")

except Exception as e:
    print(f"Произошла ошибка: {e}")
finally:
    if 'sftp' in locals():
        sftp.close()
    if 'transport' in locals():
        transport.close()


# json_file = "radiation.json"

# with open(json_file, "r", encoding="utf-8") as file:
#     json_data = json.load(file)

# df["date"] = df.apply(lambda row: f"{int(row['YEAR'])}-{int(row['MO']):02d}-{int(row['DY']):02d}", axis=1)
# df["time"] = df["HR"].apply(lambda x: f"{x:02d}:00")

# for _, row in df.iterrows():
#     date = row["date"]
#     time = row["time"]

#     if date not in json_data:
#         json_data[date] = {
#             "time": [],
#             "ALLSKY_SFC_SW_DIFF": [],
#             "CLRSKY_SFC_SW_DWN": [],
#             "ALLSKY_SFC_SW_DNI": [],
#             "ALLSKY_SFC_SW_DWN": []
#         }

#     if time in json_data[date]["time"]:
#         idx = json_data[date]["time"].index(time)
#         json_data[date]["ALLSKY_SFC_SW_DIFF"][idx] = row["ALLSKY_SFC_SW_DIFF"]
#         json_data[date]["CLRSKY_SFC_SW_DWN"][idx] = row["CLRSKY_SFC_SW_DWN"]
#         json_data[date]["ALLSKY_SFC_SW_DNI"][idx] = row["ALLSKY_SFC_SW_DNI"]
#         json_data[date]["ALLSKY_SFC_SW_DWN"][idx] = row["ALLSKY_SFC_SW_DWN"]
#     else:
#         json_data[date]["time"].append(time)
#         json_data[date]["ALLSKY_SFC_SW_DIFF"].append(row["ALLSKY_SFC_SW_DIFF"])
#         json_data[date]["CLRSKY_SFC_SW_DWN"].append(row["CLRSKY_SFC_SW_DWN"])
#         json_data[date]["ALLSKY_SFC_SW_DNI"].append(row["ALLSKY_SFC_SW_DNI"])
#         json_data[date]["ALLSKY_SFC_SW_DWN"].append(row["ALLSKY_SFC_SW_DWN"])

#     sorted_indices = sorted(range(len(json_data[date]["time"])), key=lambda i: json_data[date]["time"][i])
#     json_data[date]["time"] = [json_data[date]["time"][i] for i in sorted_indices]
#     json_data[date]["ALLSKY_SFC_SW_DIFF"] = [json_data[date]["ALLSKY_SFC_SW_DIFF"][i] for i in sorted_indices]
#     json_data[date]["CLRSKY_SFC_SW_DWN"] = [json_data[date]["CLRSKY_SFC_SW_DWN"][i] for i in sorted_indices]
#     json_data[date]["ALLSKY_SFC_SW_DNI"] = [json_data[date]["ALLSKY_SFC_SW_DNI"][i] for i in sorted_indices]
#     json_data[date]["ALLSKY_SFC_SW_DWN"] = [json_data[date]["ALLSKY_SFC_SW_DWN"][i] for i in sorted_indices]

# with open(json_file, "w", encoding="utf-8") as file:
#     json.dump(json_data, file, indent=4, ensure_ascii=False)

#rf_pred = np.where(rf_pred < 2, 0, rf_pred)

# start_time = datetime.strptime("00:00", "%H:%M")
# time_intervals = [(start_time + timedelta(hours=i)).strftime("%H:%M") for i in range(len(rf_pred))]

# tomorrow_date = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")

# result = {
#     tomorrow_date: {
#         "x": time_intervals,
#         "y": rf_pred.tolist()
#     }
# }

# script_dir = os.path.dirname(os.path.abspath(__file__))
# password_file = os.path.join(script_dir, "password.txt")
# with open(password_file, 'r') as file:
#     password = file.read().strip()

# sftp_config = {
#     "host": "istu.webappz.ru",
#     "port": 22,
#     "username": "rusvs",
#     "password": password,
#     "remote_path": "/www/solar/data.json"
# }

# local_path = os.path.join(script_dir, "data.json")

# try:
#     transport = paramiko.Transport((sftp_config["host"], sftp_config["port"]))
#     transport.connect(username=sftp_config["username"], password=sftp_config["password"])
#     sftp = paramiko.SFTPClient.from_transport(transport)

#     remote_path = sftp_config["remote_path"]
#     sftp.get(remote_path, local_path)

#     with open(local_path, "r", encoding="utf-8") as file:
#         data = json.load(file)

#     data.update(result)

#     with open(local_path, "w", encoding="utf-8") as file:
#         json.dump(data, file, ensure_ascii=False, indent=4)

#     sftp.put(local_path, remote_path)

# except Exception as e:
#     print(f"Произошла ошибка: {e}")
# finally:
#     if 'sftp' in locals():
#         sftp.close()
#     if 'transport' in locals():
#         transport.close()
