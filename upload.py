import paramiko
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
local_file = os.path.join(current_dir, "data.json")
password_file = os.path.join(current_dir, "password.txt")

try:
    with open(password_file, 'r') as file:
        password = file.read().strip()
except FileNotFoundError:
    print("Файл с паролем не найден.")
    exit(1)

sftp_config = {
    "host": "istu.webappz.ru",
    "port": 22,
    "username": "rusvs",
    "password": password,
    "remote_path": "/www/solar/data.json"
}

try:
    transport = paramiko.Transport((sftp_config["host"], sftp_config["port"]))
    transport.connect(username=sftp_config["username"], password=sftp_config["password"])
    sftp = paramiko.SFTPClient.from_transport(transport)
    sftp.put(local_file, sftp_config["remote_path"])
    print(f"Файл {local_file} успешно загружен на {sftp_config['remote_path']}.")
    sftp.close()
    transport.close()
except Exception as e:
    print(f"Произошла ошибка при передаче файла: {e}")
