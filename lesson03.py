# 1. Развернуть у себя на компьютере/виртуальной машине/хостинге MongoDB и реализовать функцию,
# которая будет добавлять только новые вакансии/продукты в вашу базу.

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from bs4 import BeautifulSoup as bs
import requests
import hashlib
import datetime as dt
from pprint import pprint

client = MongoClient('127.0.0.1', 27017)

db = client['mongo']
jobs = db.jobs

base_url = 'https://www.hh.ru/vacancies'

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36'}

keyword = input('Введите вакансию: ')

url = f'{base_url}/{keyword}'
response = requests.get(url, headers=headers)
dom = bs(response.text, 'html.parser')
vacancies = dom.find_all('div', {'class': 'vacancy-serp-item'})


# функция перебора страниц
def max_num():
    maxnum = 0
    for item in dom.find_all('a', {'data-qa': 'pager-page'}):
        maxnum = list(item.strings)[0].split(" ")[-1]
    return maxnum


max_page = int(max_num())


# Функция сбора данных
def data_collect(pages):
    vacancies_list = []
    for page in range(pages):
        url2 = f'{base_url}/{keyword}?page={page}'
        response2 = requests.get(url2, headers=headers)
        dom2 = bs(response2.text, 'html.parser')
        vacancies2 = dom2.find_all('div', {'class': 'vacancy-serp-item'})
        for vacancy in vacancies2:
            vacancy_data = {}
            vacancy_title = vacancy.find('a', {'data-qa': 'vacancy-serp__vacancy-title'}).text.strip()
            vacancy_employer = vacancy.find('div', {'class': 'vacancy-serp-item__meta-info-company'}).text.strip()
            vacancy_link = vacancy.find('a', {'data-qa': 'vacancy-serp__vacancy-title'}).get('href')

            vacancy_salary = vacancy.find('span', {'data-qa': 'vacancy-serp__vacancy-compensation'})
            vacancy_salary_data = {'min_salary': '', 'max_salary': '', 'currency': ''}
            if vacancy_salary is None:
                vacancy_salary_data['min_salary'] = 'None'
                vacancy_salary_data['max_salary'] = 'None'
                vacancy_salary_data['currency'] = 'None'
            else:
                vacancy_salary = vacancy_salary.text.replace("\u202f", '').split()
                if 'от' in vacancy_salary:
                    if 'руб.' in vacancy_salary:
                        vacancy_salary_data['min_salary'] = int(vacancy_salary[1])
                        vacancy_salary_data['max_salary'] = 'None'
                        vacancy_salary_data['currency'] = 'руб.'
                    if 'USD' in vacancy_salary:
                        vacancy_salary_data['min_salary'] = int(vacancy_salary[1])
                        vacancy_salary_data['max_salary'] = 'None'
                        vacancy_salary_data['currency'] = 'USD'
                if 'до' in vacancy_salary:
                    if 'руб.' in vacancy_salary:
                        vacancy_salary_data['min_salary'] = 'None'
                        vacancy_salary_data['max_salary'] = int(vacancy_salary[1])
                        vacancy_salary_data['currency'] = 'руб.'
                    if 'USD' in vacancy_salary:
                        vacancy_salary_data['min_salary'] = 'None'
                        vacancy_salary_data['max_salary'] = int(vacancy_salary[1])
                        vacancy_salary_data['currency'] = 'USD'
                if 'от' not in vacancy_salary and 'до' not in vacancy_salary:
                    if 'руб.' in vacancy_salary:
                        vacancy_salary_data['min_salary'] = int(vacancy_salary[0])
                        vacancy_salary_data['max_salary'] = int(vacancy_salary[2])
                        vacancy_salary_data['currency'] = 'руб.'
                    if 'USD' in vacancy_salary:
                        vacancy_salary_data['min_salary'] = int(vacancy_salary[0])
                        vacancy_salary_data['max_salary'] = int(vacancy_salary[2])
                        vacancy_salary_data['currency'] = 'USD'

            # Хешируем по ... ссылке (гарантия уникальности)
            link_pre_encode = vacancy_link.encode()
            link_encode = hashlib.sha256(link_pre_encode)
            link_hex = link_encode.hexdigest()

            # Добавляем новое поле ID. И timestamp
            vacancy_data['_id'] = link_hex
            vacancy_data['vacancy_title'] = vacancy_title
            vacancy_data['vacancy_employer'] = vacancy_employer
            vacancy_data['vacancy_link'] = vacancy_link
            vacancy_data['vacancy_salary'] = vacancy_salary_data
            vacancy_data['time_added'] = dt.datetime.now()

            # Добавляем в коллекцию через try except
            try:
                jobs.insert_one(vacancy_data)
            except DuplicateKeyError:
                print(f"Document with id = {link_hex} already exists")


data_collect(max_page)

# 2. Написать функцию, которая производит поиск и выводит на экран вакансии с заработной платой
# больше введённой суммы (необходимо анализировать оба поля зарплаты).
# Для тех, кто выполнил задание с Росконтролем - напишите запрос для поиска продуктов с рейтингом не ниже введенного
# или качеством не ниже введенного (то есть цифра вводится одна, а запрос проверяет оба поля)

salary_use = int(input('Введите минимальный порог заработной платы: '))


def salary_search(salary_use):
    for a in jobs.find(
            {'$or': [{"vacancy_salary.min_salary": {'$gt': salary_use}},
                     {"vacancy_salary.max_salary": {'$gt': salary_use}}]}):
        pprint(a)


salary_search(salary_use)