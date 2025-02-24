from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import re
import pandas as pd
import os
from datetime import datetime, timedelta
import json

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

url = "https://rp5.ru/Погода_в_Иркутске"
driver.get(url)

wait = WebDriverWait(driver, 15)
button = wait.until(EC.element_to_be_clickable((By.ID, "ftab-0")))
button.click()

table = wait.until(EC.presence_of_element_located((By.ID, "forecastTable_1_3")))
rows = table.find_elements(By.TAG_NAME, "tr")

data = []

hours_raw = rows[1].find_elements(By.TAG_NAME, "td") or rows[1].find_elements(By.TAG_NAME, "th")
"""for i in hours_raw:
    print(i.text)"""
hours = [int(hour.text) for hour in hours_raw[1:-1]]

months_lib = {"января" : 1, "февраля" : 2, "марта" : 3, "апреля" : 4, "мая" : 5, "июня" : 6, 
          "июля" : 7, "августа" : 8, "сентября" : 9, "октября" : 10, "ноября" : 11, "декабря" : 12,}
cells = rows[0].find_elements(By.TAG_NAME, "td") or rows[0].find_elements(By.TAG_NAME, "th")
cells = [txt.text for txt in cells]
days = []
months = []
for cell in cells:
    date = re.search(r"(\d+)\s+([а-яА-Я]+)", cell)
    if date:
        day = int(date.group(1))
        month = months_lib[date.group(2)]
        days.append(day)
        months.append(month)
data.append(hours)

cells = rows[2].find_elements(By.TAG_NAME, "td") or rows[2].find_elements(By.TAG_NAME, "th")
cloud_cover = []
clouds = []
cloud_percentages = []

for cell in cells:
    try:
        cc_0 = cell.find_element(By.CLASS_NAME, "cc_0").get_attribute("innerHTML")

        teg_b = re.search(r"<b>(.*?)</b>", cc_0)
        cloud_cover.append(teg_b.group(1) if teg_b else '')

        teg_br = re.search(r"<br/>\((.*?)\)", cc_0)
        cloud_info = teg_br.group(1).strip('"') if teg_br else ''

        lower = re.search(r"нижнего яруса (\d+)%", cloud_info)
        middle = re.search(r"среднего яруса (\d+)%", cloud_info)

        if lower:
            cloud_percentages.append(int(lower.group(1)))
        elif middle:
            cloud_percentages.append(int(middle.group(1)))
        else:
            cloud_percentages.append(0)

        clouds.append(cloud_info)

    except:
        pass

data.append(cloud_cover[1:-1])
cloud_percentages[1:-1] = [x / 100 for x in cloud_percentages[1:-1]]
data.append(cloud_percentages[1:-1])

cells = rows[3].find_elements(By.TAG_NAME, "td") or rows[3].find_elements(By.TAG_NAME, "th")
rainfall = []
for cell in cells:
    try:
        pr_0 = cell.find_element(By.CLASS_NAME, "pr_0")
        pr_0 = pr_0.get_attribute("outerHTML")
        rf = re.search(r"tooltip\(this, '(.*?)'", pr_0)
        if rf:
            rainfall.append(rf.group(1))
        else:
            rainfall.append('')
    except:
        pass
data.append(rainfall[1:-1])

for i in range(4, 11):
    raw_data = rows[i].find_elements(By.TAG_NAME, "td") or rows[i].find_elements(By.TAG_NAME, "th")
    raw_data = [raw.text for raw in raw_data]
    data.append(raw_data[1:-1])

hum_data = rows[11].find_elements(By.TAG_NAME, "td") or rows[11].find_elements(By.TAG_NAME, "th")
humidity = []
for cell in hum_data:
    digit = cell.get_attribute("innerHTML")
    teg_b = re.search(r"<b>(.*?)</b>", digit)
    if teg_b:
        humidity.append(teg_b.group(1))
    else:
        humidity.append(digit)
data.append(humidity[1:-1])

df = pd.DataFrame(data).T  

first_zero_hour_index = df[df[0] == 0].index[0]

current_date = datetime.today()

if df.iloc[0, 0] == 0:
    current_date += timedelta(days=1)

years, months, days = [], [], []

previous_hour = df.iloc[0, 0]
track_hour_decrease = False

for i in range(len(df)):
    current_hour = df.iloc[i, 0]

    if i == first_zero_hour_index:
        track_hour_decrease = True

    if track_hour_decrease and current_hour < previous_hour:
        current_date += timedelta(days=1)

    years.append(current_date.year)
    months.append(current_date.month)
    days.append(current_date.day)

    previous_hour = current_hour

df['YEAR'] = years
df['MO'] = months
df['DY'] = days

df = df[['YEAR', 'MO', 'DY'] + [col for col in df.columns if col not in ['YEAR', 'MO', 'DY']]]

df.columns = ['YEAR','MO','DY','HR','N','Nh','W1','F','T','Tt','Po','Ff','FF','f','U']
columns = ['F','Tt','FF','f']
df = df.drop(columns, axis=1)

json_dir = os.path.dirname(os.path.abspath(__file__))
json_file = os.path.join(json_dir, "weather_to_num.json") 
with open(json_file , 'r', encoding='utf-8') as f:
    replacement_rules = json.load(f)

def normalize_text(text):
    replacements = {
        'C': 'С',
        'c': 'с',
    }
    for latin, cyrillic in replacements.items():
        text = text.replace(latin, cyrillic)
    return text.strip()

def replace_weather_condition(text, condition_dict):
    text = normalize_text(text)
    for condition, value in condition_dict.items():
        if condition.lower() in text.lower():
            return value
    return text

df['W1'] = df['W1'].apply(lambda x: replace_weather_condition(str(x), replacement_rules["W1"]))
df['N'] = df['N'].apply(lambda x: replace_weather_condition(str(x), replacement_rules["N"]))

rad = "rad.csv"
script_dir = os.path.dirname(os.path.abspath(__file__))
rad = os.path.join(script_dir, rad)
df2 = pd.read_csv(rad, delimiter=';', encoding='utf-8', index_col=False)
df = pd.merge(df, df2[['MO', 'DY', 'HR', 'sinα', 'Ho']], on=['MO', 'DY', 'HR'], how='left')

import joblib
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime, timedelta
import paramiko

script_dir = os.path.dirname(os.path.abspath(__file__))
rf_model = os.path.join(script_dir, 'model.pkl')
rf_model = joblib.load(rf_model)

data_test = df.copy()

data_test['MO'] = data_test['MO'].astype(int)
data_test['DY'] = data_test['DY'].astype(int)

data_test['DayOfYear'] = pd.to_datetime(
    data_test[['YEAR', 'MO', 'DY']].astype(str).agg('-'.join, axis=1), errors='coerce'
).dt.dayofyear.fillna(0).astype(int)

data_test['sin_month'] = np.sin(2 * np.pi * data_test['MO'] / 12)
data_test['cos_month'] = np.cos(2 * np.pi * data_test['MO'] / 12)

data_test['sin_hour'] = np.sin(2 * np.pi * data_test['HR'].astype(int) / 24)
data_test['cos_hour'] = np.cos(2 * np.pi * data_test['HR'].astype(int) / 24)
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


