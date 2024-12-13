import requests
import re
import gzip
import shutil
import os

def get_weather(date_begin, date_end):
    url_get = 'https://rp5.ru/'
    url_post = 'https://rp5.ru/responses/reFileSynop.php'
    session = requests.Session()
    session.get(url_get)

    payload = {
        'wmo_id': '30710',
        'a_date1': date_begin,
        'a_date2': date_end,
        'f_ed3': '10',
        'f_ed4': '10',
        'f_ed5': '14',
        'f_pe': '1',
        'f_pe1': '1',
        'lng_id': '2',
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 YaBrowser/24.7.0.0 Safari/537.36',
        'Accept': 'text/html, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'ru,en;q=0.9',
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://rp5.ru/',
        'Origin': 'https://rp5.ru',
        'Connection': 'keep-alive',
    }
    response = session.post(url_post, data=payload, headers=headers)

    if response.status_code == 200:
        #print(response.text)
        match = re.search(r'href=["\']?(https://[^\s"\'<>]+\.csv\.gz)["\']?', response.text)
        if match:
            download_url = match.group(1)
            print(f'Ссылка для скачивания: {download_url}')
            
            download_response = session.get(download_url)
            
            if download_response.status_code == 200:
                script_dir = os.path.dirname(os.path.abspath(__file__))              
                compressed_file = os.path.join(script_dir, 'weather_data.csv.gz')
                with open(compressed_file, 'wb') as file:
                    file.write(download_response.content)
                print('Файл успешно загружен и сохранен.')
                
                output_file = os.path.join(script_dir, f'data/{date_begin}-{date_end}.csv')
                with gzip.open(compressed_file, 'rb') as f_in:
                    with open(output_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                print(f'Файл {compressed_file} успешно распакован в {output_file}.')
                os.remove(compressed_file)

                with open(output_file, 'r', encoding='windows-1251') as f:
                    lines = f.readlines()
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.writelines(lines[6:])
            else:
                print(f'Ошибка при скачивании файла: {download_response.status_code}')
        else:
            print('Не удалось найти ссылку для скачивания.')
    else:
        print(f'Произошла ошибка: {response.status_code}, сообщение: {response.text}')

date_begin = "30.06.2017"
date_end = "30.06.2017"

get_weather(date_begin, date_end)
