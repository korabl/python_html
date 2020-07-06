from lxml import html
import requests, pymongo
from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client['news']

news = db.news

header = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
         'Accept':'*/*'}

def get_dom(link):
    response = requests.get(link, headers=header).text
    dom = html.fromstring(response)
    return dom

def get_news_lenta():
    dom = get_dom('https://lenta.ru/')
    lenta_news_list = []
    items = dom.xpath("//section[@class='row b-top7-for-main js-top-seven']//div[@class='span4']//div[contains(@class,'item')]")

    for item in items:
        news = {}
        name = item.xpath(".//text()")
        link = item.xpath(".//a//@href")
        date = item.xpath(".//time/text()")

        news['source'] = 'Lenta.ru'
        news['name'] = name[1]
        news['date'] = date
        news['link'] = link

        lenta_news_list.append(news)

    return(lenta_news_list)


def get_news_mail():
    dom = get_dom('https://news.mail.ru/')

    mail_news_list = []
    items_main = dom.xpath("//div[@name='clb20268373']//div[@class='cols__wrapper']/div/div/div")

    for item in items_main:
        news = {}
        name = item.xpath(".//span[contains(@class, 'newsitem__title-inner')]/text()")
        link = str(item.xpath(".//a[contains(@class, 'newsitem__title')]/@href")[0])
        date = item.xpath(".//span[contains(@class, 'newsitem__param')]/text()")

        news['source'] = date[1]
        news['name'] = name
        news['date'] = date[0]
        news['link'] = link

        mail_news_list.append(news)

    items = dom.xpath("//div[@name='clb20268373']//div[@class='cols__wrapper']//li")
    for item in items:
        news = {}
        name = item.xpath(".//span[contains(@class, 'link__text')]/text()")
        link = str(item.xpath(".//a[contains(@class, 'link_flex')]/@href")[0])
        dom = get_dom(link)

        date = dom.xpath("//span[@class='note__text breadcrumbs__text js-ago']/text()")
        source = dom.xpath("//a[@class='link color_gray breadcrumbs__link']//span[@class='link__text']/text()")

        news['source'] = source
        news['name'] = name
        news['date'] = date
        news['link'] = link

        mail_news_list.append(news)

    return mail_news_list


def get_news_ya():
    dom = get_dom('https://yandex.ru/news/')
    ya_news_list = []
    items = dom.xpath("//div[contains(@class, 'news-app__content')]//div[contains(@class, 'news-top-stories')]//div//article")
    print(len(items))

    for item in items:
        news = {}
        name = item.xpath(".//h2/text()")
        link = item.xpath(".//a[contains(@class, 'news-card__link')]/@href")
        date = item.xpath("//span[@class='mg-card-source__time']/text()")
        source = item.xpath("//span[@class='mg-card-source__source']/text()")

        news['source'] = source
        news['name'] = name
        news['date'] = date
        news['link'] = link

        ya_news_list.append(news)

    return ya_news_list

#Добавляем в БД
lenta = get_news_lenta()
mail = get_news_mail()
ya = get_news_ya()
news.insert_many(lenta)
news.insert_many(mail)
news.insert_many(ya)


i = 0
for n in news.find({}):
    i += 1
print(f'Новостей : {i}')
