import requests
from bs4 import BeautifulSoup
from datetime import date
import xlsxwriter

from models import Catalog, Product

SITE_URL = 'https://www.mebelaero.ru'
MAIN_CATALOG_URL = 'https://www.mebelaero.ru/catalog/'


# возвращает список из объектов Catalog
def get_parsed_catalogs():
    # получаем страницу каталога
    page = requests.get(MAIN_CATALOG_URL)

    # проверяем на статус OK
    if page.status_code != 200:
        return []

    # создаем объект BeautifulSoup
    soup = BeautifulSoup(page.content, 'html.parser')
    # находим все элементы которые содержат класс "catblock"(блок содержит множество категорий)
    results = soup.find_all(class_='catblock')
    catalog_list = []

    # проходимся по всем элементам "catblock" и добавляем в массив каталогами Catalog
    for result in results:
        catalog_list += get_catalog_list(result)

    return catalog_list


# принимает в параметре объекты содержащие элементы каталогов
# возвращает массив из объектов Catalog
def get_catalog_list(catalog_elements):
    catalog_elements = catalog_elements.find_all('a')
    catalogs = []
    for cat_element in catalog_elements:
        title = cat_element.text.strip()
        link = cat_element['href']

        if None in (title, link):
            continue

        category = Catalog()
        category.name = title
        category.link = check_and_get_link(link)

        catalogs.append(category)

    return catalogs


# возвращает список из объектов Product
def get_parsed_products(catalogs):
    products_list = []

    for catalog in catalogs:
        results = link2products_list(catalog.link)
        products_list += results
        print("Каталог: " + catalog.name + " url: " + catalog.link + "продуктов: (" + str(len(results)) + ")")

    print("====================")
    return products_list


# метод принимает в аргумент ссылку и возвращает массив из объектов Product
def link2products_list(link):
    # создаем массив где будем ложить спарсенные объекты Product
    product_list = []
    # получаем страницу из ссылки
    page = requests.get(link)

    # проверка на статус OK
    if page.status_code != 200:
        return product_list

    soup = BeautifulSoup(page.content, 'html.parser')
    item_list = soup.find_all(class_='item_list tile')

    # получаем массив продуктов (Product) из элемента li
    for items in item_list:
        products_elements = items.find_all('li')
        if products_elements is not None:
            product_list += parse_product_elements(products_elements)

    # получаем ссылку с на слующую страницу пагинации и если имеется ссылка
    # РЕКУРСИВНО вызываем "link2products"
    next_page = soup.find('li', class_='right active')
    if next_page is not None:
        next_page_link = next_page.find('a')['href']
        next_page_link = check_and_get_link(next_page_link)
        product_list += link2products_list(next_page_link)

    return product_list


# принмает список элементов li где содержатся информация из продуктов
# и возвращает список продуктов
def parse_product_elements(products_elements):
    product_list = []

    for li_element in products_elements:
        tag_a = li_element.find('div', class_='desc').find('a')
        div_price = li_element.find('div', class_='price')

        if tag_a is None:
            continue

        name = tag_a.text
        link = tag_a['href']
        price = ''

        if div_price is not None:
            price = div_price.find('span').next

        if None in (name, link):
            continue

        product = Product()
        product.name = name
        product.link = check_and_get_link(link)
        product.price = price

        product_list.append(product)

    return product_list


# принимает в аргументе строку содержащую ccылку
# проверяет является ли ссылка абсолютной или относительной
# в любом случае возвращает абсолютную ссылку
def check_and_get_link(link):
    if 'mebelaero.ru' not in link:
        link = SITE_URL + link
    return link


# принимает массив из объектов Product и название сохраняемого excel файла
# и сохраняет данные в файл excel
def save_to_excel_file(items, filename='mebelaero.xlsx', ):
    # создаем файл excel .xlsx и добавляем страницу
    workbook = xlsxwriter.Workbook(filename)
    worksheet = workbook.add_worksheet()

    # строка и колонка
    row = 0
    col = 0

    # проходимся по массиву и сохраняем данные
    for item in items:
        worksheet.write(row, col, item.name)
        worksheet.write(row, col + 1, item.price)
        worksheet.write(row, col + 2, item.link)
        row += 1

    # закрываем excel
    workbook.close()


if __name__ == '__main__':
    # получаем список каталогов
    catalogs_list = get_parsed_catalogs()

    # получаем список всех продуктов из каталогов
    products = get_parsed_products(catalogs_list)

    # сохраняем в excel файл если список продуктов не пуст
    isEmpty = (len(products) == 0)
    if not isEmpty:
        # формируем название excel файла по дате
        path_to_file = 'results/mebelaero-' + str(date.today()) + '.xlsx'

        # убираем дубликаты
        uniq_products = list(set(products))

        # cохраняем уникальные продукты в excel файле
        save_to_excel_file(uniq_products, filename=path_to_file)

        print("Сайт успешно спарсен.")
        print("Результат сохранен в файле " + path_to_file)
        print("Всего уникальных позиций: " + str(len(uniq_products)))
        print("Всего позиций спарсено: " + str(len(products)))
    else:
        print("Список продуктов пуст!")
