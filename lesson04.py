# 1 Написать приложение, которое собирает основные новости с сайта на выбор
# news.mail.ru, lenta.ru, yandex-новости.
# Для парсинга использовать XPath. Структура данных должна содержать:
# название источника;
# наименование новости;
# ссылку на новость;
# дата публикации.

from lxml import html
import requests
from pymongo import MongoClient


url = 'https://lenta.ru/parts/news/'
header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36'}

response = requests.get(url, headers=header)
dom = html.fromstring(response.text)
news_list = dom.xpath("(//li[contains(@class,'parts-page__item')])[position() < last()]")

news = []
for el in news_list:
    info = {}

    name = el.xpath(".//h3//text()")
    link = el.xpath(".//a/@href")

    info['source'] = 'lenta'
    info['name'] = name[0]
    info['link'] = link[0]
    _, _, year, month, day, *_ = link[0].split('/')
    info['date'] = f'{year}-{month}-{day}'

    news.append(info)



# 2 Сложить собранные новости в БД
# Минимум один сайт, максимум - все три

client = MongoClient('127.0.0.1', 27017)
mongodb = client['news']
newsdb = mongodb.newsdb

for el in news:
    try:
        el['_id'] = el['link']
        newsdb.insert_one(el)
    except Exception as e:
        print('Ошибка добавления новости!')
        print(e)