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
"""day_data = []
month_data = []
for i in range(7*4 - len(hours)):
    day_data.append(days[0])
    month_data.append(months[0])
for i in range(1, 7):
    for j in range(4):
        day_data.append(days[i])
        month_data.append(months[i])
data.append(month_data)
data.append(day_data)"""
data.append(hours)

cells = rows[2].find_elements(By.TAG_NAME, "td") or rows[2].find_elements(By.TAG_NAME, "th")
cloud_cover = []
clouds = []
for cell in cells:
    try:
        cc_0 = cell.find_element(By.CLASS_NAME, "cc_0")
        cc_0 = cc_0.get_attribute("innerHTML")
        teg_b = re.search(r"<b>(.*?)</b>", cc_0)
        if teg_b:
            cloud_cover.append(teg_b.group(1))
        else:
            cloud_cover.append('')
        teg_br = re.search(r"<br/>\((.*?)\)", cc_0)
        if teg_br:
            clouds.append(teg_br.group(1).strip('"'))
        else:
            clouds.append('')
    except:
        pass
data.append(cloud_cover[1:-1])
#data.append(clouds[1:-1])

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

df = pd.DataFrame(data)
df = df.T
index_of_zero = df[df[0] == 0].index[0]
df = df.iloc[index_of_zero:index_of_zero+24]

tomorrow = datetime.today() + timedelta(days=1)

tomorrow_year = tomorrow.year
tomorrow_month = tomorrow.month
tomorrow_day = tomorrow.day
df['year'] = [tomorrow_year] * 24
df['month'] = [tomorrow_month] * 24
df['day'] = [tomorrow_day] * 24

df = df[['year', 'month', 'day'] + [col for col in df.columns if col not in ['year', 'month', 'day']]]

df.columns = ['YEAR','MO','DY','HR','N','W1','F','T','Tt','Po','Ff','FF','f','U']
columns = ['F','Tt','FF','f']
df = df.drop(columns, axis=1)

json_dir = os.path.dirname(os.path.abspath(__file__))
json_file = os.path.join(json_dir, "weather.json") 
with open(json_file , 'r', encoding='utf-8') as f:
    replacement_rules = json.load(f)

def replace_weather_condition(text, condition_dict):
    for condition, value in condition_dict.items():
        if re.search(condition, text, re.IGNORECASE):
            return value
    return text

df['W1'] = df['W1'].apply(lambda x: replace_weather_condition(x, replacement_rules["W1"]))
df['N'] = df['N'].apply(lambda x: replace_weather_condition(x, replacement_rules["N"]))

rad = "rad.csv"
script_dir = os.path.dirname(os.path.abspath(__file__))
rad = os.path.join(script_dir, rad)
df2 = pd.read_csv(rad, delimiter=';', encoding='utf-8', index_col=False)
df2['sinα'] = df2['sinα'].str.replace(',', '.').astype(float)
df2['Ho'] = df2['Ho'].str.replace(',', '.').astype(float)
df = pd.merge(df, df2[['MO', 'DY', 'HR', 'sinα', 'Ho']], on=['MO', 'DY', 'HR'], how='left')

file = os.path.join(script_dir, "data/" + "data.csv")
df.to_csv(file, index=False, encoding="utf-8")
