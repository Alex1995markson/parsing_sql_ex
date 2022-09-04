import os
import time
import json
import requests
import lxml
from bs4 import BeautifulSoup, element
from seleniumwire import webdriver
from requests.structures import CaseInsensitiveDict
from connect_to_db import series_collection


from dotenv import load_dotenv


load_dotenv()

headers = CaseInsensitiveDict()

# header = {
# "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9", 
# "Accept-Encoding": "gzip, deflate", 
# "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8", 
# "Dnt": "1", 
# "Upgrade-Insecure-Requests": "1", 
# "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36", 
# }

PATH_TO_DRIVER = os.getenv('PATH_TO_DRIVER')
URL = os.getenv('DEFAULT_URL')

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--incognito")


def initicialization_brower() -> None:
    cookie = ""
    driver = webdriver.Chrome(PATH_TO_DRIVER, chrome_options=chrome_options)
    driver.get(URL)
    driver.implicitly_wait(15)
    driver.find_element('name', 'login').send_keys(os.getenv('LOGIN'))
    driver.find_element('name', 'psw').send_keys(os.getenv('PASSWORD'))
    driver.find_element('name', 'subm1').click()
    driver.implicitly_wait(15)
    for request in driver.requests:
        # print(type(request.response.headers['Set-Cookie']))
        # print('-------------')
        if (request.response.headers['Set-Cookie']):
            if ((request.response
                 .headers['Set-Cookie'].startswith('PHPSESSID'))):
                cookie = request.response.headers['Set-Cookie']
                break
    return cookie
    time.sleep(20)
    driver.implicitly_wait(30)
    driver.close()


def insert_to_db(collection, data):
    return collection.insert_one(data).inserted_id


def delete_tags(str_):
    return str_.replace('<td>', '').replace('</td>', '')


def parse_html(r):

    name = '-'
    full_name = '-'
    login = '-'
    img_src = '-'
    name_crt = '-'
    name_link_crt = '-'
    city = '-'
    country = '-'
    birthday = '-'
    education = '-'
    direction_edu = '-'
    email = '-'
    other_info = ''

    rec = {}

    try:
        if r.status_code == 200:
            html = r.text
            soup = BeautifulSoup(html, 'html.parser')
            table_html = (soup.
                          find_all('td', {'align': 'center', 'width': '80%'})
                          or None)

            name = table_html[0].find('img')['alt'] or None
            full_name = (name[0:name.index('(')]) or None
            login = name[name.index('(')+1:len(name)-2] or None  # login
            img_src = table_html[0].find('img')['src'] or None  # path image
            # print(name, full_name, full_name, login, img_src)
            # print('--------------')
            try:
                tags_td = table_html[0].find_all('table', {'border': '0',
                                                           'cellpadding': '0',
                                                           'cellspacing': '5'})[1]
                # print(tags_td)
                for item in tags_td.find_all('td', {'valign': None}):
                    name_crt = (item.text[0:item.text.index('\n')] or None)  # Cert
                    name_link_crt = item.find('a')['href'] or None  # link to Cert

                info = table_html[0].find_all('table',{'border': '0',
                                                        'cellpadding': '0',
                                                        'cellspacing': '2'
                                                        })[0].find_all('td') or None
                # print('--------------')
                # print(type(info))
                # print(len(info))
                for item in range(0, len(info)-1):
                    # print(str(info[item]))
                    if (str(info[item]) == '<td>Страна:</td>'):
                        country = delete_tags(str(info[item+1]))
                    if (str(info[item]) == '<td>Город:</td>'):
                        city = delete_tags(str(info[item+1]))
                    if (str(info[item]) == '<td>Дата рождения:</td>'):
                        birthday = delete_tags(str(info[item+1]))
                    if (str(info[item]) == '<td>Вуз:</td>'):
                        education = delete_tags(str(info[item+1]))
                    if (str(info[item]) == '<td>Специальность:</td>'):
                        direction_edu = delete_tags(str(info[item+1]))
                    if (str(info[item]) == '<td>E-Mail:</td>'):
                        email = delete_tags(str(info[item+1]))
                    # else:
                    #     other_info += info[item]



            except Exception as ex:
                print('Inner block with cert and additional info is broken s')
                tags_td = None
                info = None

            rec = {'name': name,
                   'full_name': full_name,
                   'login': login,
                   'img': img_src,
                   'certification': name_crt,
                   'link_certification': name_link_crt,
                   'country': country,
                   'city': city,
                   'birthday': birthday,
                   'education': education,
                   'direction_education': direction_edu,
                   'email': email,
                   'additional_info': other_info}
    except Exception as ex:
        print('Exception while parsing')
        print(str(ex))
    finally:
        return rec


def main():
    current_position = 0 + 1
    response = ""
    get_cookie = initicialization_brower()
    headers["Cookie"] = get_cookie
    while(current_position < 100000000):
        response = (requests.get(f'https://sql-ex.ru/users_page.php?uid={current_position}', headers=headers))
        json_data = parse_html(response)
        insert_to_db(series_collection, json_data)
        # print(json_data)
        current_position += 1


if __name__ == '__main__':
    main()
