# 1. Посмотреть документацию к API GitHub,
# разобраться как вывести список наименований репозиториев для конкретного пользователя,
# сохранить JSON-вывод в файле *.json.

import requests
import time
import json
from pprint import pprint

def get_data(url: str) -> dict:
    while True:
        time.sleep(1)
        response = requests.get(url)
        if response.status_code == 200:
            break
    return response.json()

username = input('Введите username: ')
username = 'vit050587' if username == '' else username
url = 'https://api.github.com/users/'+username+'/repos'

response = get_data(url)
repo = []
for itm in response:
    repo.append(itm['name'])
print(f'Список репозиториев пользователя {username}\n', '*' * 50)
pprint(repo)

with open('1_1_repo.json', 'w') as f:
    json_repo = json.dump(repo, f)




# 2. Изучить список открытых API
# (https://www.programmableweb.com/category/all/apis).
# Найти среди них любое, требующее авторизацию (любого типа).
# Выполнить запросы к нему, пройдя авторизацию. Ответ сервера записать в файл.
# Если нет желания заморачиваться с поиском, возьмите API вконтакте
# (https://vk.com/dev/first_guide).
# Сделайте запрос, чтобы получить список всех сообществ на которые вы подписаны.