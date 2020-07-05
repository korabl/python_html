import requests, pymongo, re
from bs4 import BeautifulSoup as bs
from pymongo import MongoClient
from pprint import pprint

client = MongoClient('localhost', 27017)
db = client['vacancies']

vacancy_db = db.vacancy_db

header = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
         'Accept':'*/*'}

# time_to_sleep_when_captcha = 1
main_link_hh = 'https://hh.ru'
main_link_sj = 'https://russia.superjob.ru'
# job_name = str(input('Введите должность: '))
job_name = 'Data+scientist'

url_hh = f'/search/vacancy?L_is_autosearch=false&clusters=true&enable_snippets=true&text={job_name}&page=0'
url_sj = f'/vacancy/search/?keywords={job_name}'



# Обработка зарплаты
def salary_parser(salary_string):
    salary_string = re.sub('(?<=\d)\s(?=\d)', '', salary_string)
    salary_string = salary_string.lower()
    words = re.findall(r'\w+', salary_string)

    salary_from, salary_to, salary_currency = None, None, None

    if words:
        if len(words) > 2:
            salary_currency = words[2]

        if words.count('от') != 0:
            salary_from = int(words[1])
        elif words.count('до') != 0:
            salary_to = int(words[1])
        elif words.count('по') != 0:
            pass
        else:
            salary_from = int(words[0])
            salary_to = int(words[1])

    return salary_from, salary_to, salary_currency

# Получение супа с hh
def get_new_soup_hh(url_hh):
    response_hh = requests.get(main_link_hh + url_hh, headers=header).text
    soup_hh = bs(response_hh,'lxml')
    return soup_hh

def get_new_vacancy_list_hh(soup_hh):
    vacancy_block_hh = soup_hh.find('div', {'class':'vacancy-serp'})
    vacancy_list_hh = vacancy_block_hh.find_all('div', {'class':'vacancy-serp-item'})
    return vacancy_list_hh

# Получение супа с sj
def get_new_soup_sj(url_sj):
    response_sj = requests.get(main_link_sj + url_sj, headers=header).text
    soup_sj = bs(response_sj,'lxml')
    return soup_sj

def get_new_vacancy_list_sj(soup_sj):
    vacancy_block_sj = soup_sj.find('div', {'class': '_1ID8B'})
    vacancy_list_sj = vacancy_block_sj.find_all('div', {'class': 'f-test-vacancy-item'})
    return vacancy_list_sj

#Получение id
def get_id(link):
    id = re.sub(r'\D', '', link)
    return id

# Получение вакансий с hh
def get_vacancies_hh(v_list, soup_hh):
    for vacancy in v_list:
        vacancy_data_hh = {}
        vacancy_name = vacancy.find('a', {'class': 'bloko-link'}).getText()
        vacancy_link = vacancy.find('a', {'class': 'bloko-link'})['href']
        vacancy_site = main_link_hh

        salary_string = vacancy.find('div', {'class': 'vacancy-serp-item__sidebar'}).getText().replace(u'\xa0', u'')

        vacancy_data_hh['salary_from'], vacancy_data_hh['salary_to'], vacancy_data_hh['salary_currency'] = salary_parser(
            salary_string)
        vacancy_data_hh['name'] = vacancy_name
        vacancy_data_hh['link'] = vacancy_link
        vacancy_data_hh['site'] = vacancy_site
        vacancy_data_hh['_id'] = get_id(vacancy_link)

        # Добавляем в БД
        try:
            vacancy_db.insert_one(vacancy_data_hh)
        except pymongo.errors.DuplicateKeyError:
            pass

    # sleep(time_to_sleep_when_captcha)
    next_button_link_hh = soup_hh.find('a', {'class': 'HH-Pager-Controls-Next'})['href']
    return next_button_link_hh

while True:
    soup_hh = get_new_soup_hh(url_hh)
    vacancy_list_hh = get_new_vacancy_list_hh(soup_hh)
    try:
        url_hh = get_vacancies_hh(vacancy_list_hh, soup_hh)
    except TypeError:
        break

# Получение вакансий с sj
def get_vacancies_sj(v_list, soup_sj):
    for vacancy in v_list:
        vacancy_data_sj = {}
        vacancy_name = vacancy.find('a', {'class': 'icMQ_'})
        if vacancy_name:
            vacancy_data_sj['name'] = vacancy_name.getText()
        url_block = vacancy.find('a', {'class': 'icMQ_'})
        if url_block:
            vacancy_data_sj['url'] = main_link_sj + url_block['href']
            vacancy_data_sj['source'] = 'superjob.ru'
        vacancy_salary = vacancy.find('span', {'class': '_3mfro'})
        if vacancy_salary:
            salary_string = vacancy_salary.getText().replace(u'\xa0', u' ')
            vacancy_data_sj['salary_from'], vacancy_data_sj['salary_to'], vacancy_data_sj['salary_currency'] = salary_parser(
                salary_string)
        vacancy_data_sj['site'] = main_link_sj
        vacancy_data_sj['_id'] = get_id(url_block['href'])

        # Добавляем в БД
        try:
            vacancy_db.insert_one(vacancy_data_sj)
        except pymongo.errors.DuplicateKeyError:
            pass

    # sleep(time_to_sleep_when_captcha)
    next_button_link_sj = main_link_sj + soup_sj.find('a', {'class': 'f-test-link-Dalshe'})['href']
    return next_button_link_sj


while True:
    soup_sj = get_new_soup_sj(url_sj)
    vacancy_list_sj = get_new_vacancy_list_sj(soup_sj)
    try:
        url_sj = get_vacancies_sj(vacancy_list_sj, soup_sj)
    except TypeError:
        break

i = 0
for item in vacancy_db.find({}):
    i += 1
print(f'Вакансий : {i}')

# Очистка базы
# db.vacancy_db.delete_many({})

def print_vacs(salary):
    for item in vacancy_db.find({'$or':[{'salary_from': {'$gt': sum}, 'salary_to': {'$gt': sum}}]}):
        pprint(item)

sum = int(input('Вывести вакансии с зарплатой выше (рублей): '))
print_vacs(sum)

