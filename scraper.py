import re
from contextlib import contextmanager
from bs4 import BeautifulSoup
#from slugify import slugify_unicode
from slugify import slugify
import concurrent.futures
import pandas as pd
import requests
import time
import csv
import os

# Variables globales
base_url = "http://books.toscrape.com/"
home_url = "https://books.toscrape.com/index.html"
base_page_url = "http://books.toscrape.com/catalogue/category/books/"
base_book_url = "http://books.toscrape.com/catalogue/"


session = requests.Session()


def timer(func):
    """Fonction permettant de chronométrer l'exécution d'une fonction

    Arguments:
        func {function} -- fonction à chronométrer

    Returns:
        function -- fonction chronométrée
    """
    def wrapper(*args, **kwargs):
        t_start = time.time()
        pf_start = time.perf_counter()

        result = func(*args, **kwargs)

        t_end = time.time()
        pf_end = time.perf_counter()
        print(f"Execution time with perf_counter: {pf_end - pf_start} seconds")
        print("{} - Done in {:.3f}s".format(func.__name__, t_end - t_start))
        return result
    return wrapper


@timer
def get_page_content(url, parser="lxml"):
    """
    Fonction permettant de traiter les requêtes et recupérer le contenu d'une page donnée

    Arguments:
        url: url de la page à traiter
        parser: parser à utiliser pour traiter le contenu de la page

    Returns:
        BeautifulSoup: objet BeautifulSoup contenant le contenu de la page
    """

    response = session.get(url)
    if not response.ok:
        print("Error: ", response.status_code)
        return None
    else:
        response.encoding = "utf-8"
        content = response.content
        extracted_soup = BeautifulSoup(content, parser)
        return extracted_soup


@timer
def extract_single_book_content(url):
    """Fonction permettant de récupérer les données d'un seul produit

    Arguments:
        url {string} -- url du produit à traiter

    Returns:
        dict -- dictionnaire contenant les données du produit
    """

    soup = get_page_content(url)

    if soup is None:
        return None
    else:
        book_availability = soup.find_all(
            "table", class_="table table-striped")[0].findAll('tr')[5].td.text
        book_rating = soup.find_all(
            "div", class_="col-sm-6 product_main")[0].findAll('p')[2].get('class')[1]
        book_upc = soup.find_all(
            "table", class_="table table-striped")[0].findAll('tr')[0].td.text
        book_category = soup.find_all("ul", class_="breadcrumb")[
            0].findAll('a')[2].text
        book_title = soup.find_all(
            "div", class_="col-sm-6 product_main")[0].h1.text
        book_price = soup.find_all(
            "div", class_="col-sm-6 product_main")[0].p.text.lstrip("Â")
        price_ex_tax = soup.find_all(
            "table", class_="table table-striped")[0].findAll('tr')[2].td.text
        book_tax = soup.find_all(
            "table", class_="table table-striped")[0].findAll('tr')[4].td.text

        book_desc = soup.find_all("p")[3].text
        book_img_extracted_link = soup.find_all(
            "div", class_="item active")[0].img['src']
        book_img_full_link = base_url + \
            book_img_extracted_link.lstrip("../../../")

        single_book_infos = {
            'book_upc': book_upc,
            'book_category': book_category,
            "book_title": str(book_title),
            "book_price": book_price,
            "price_exc_tax": price_ex_tax,
            "tax": book_tax,
            "book_rating": book_rating,
            'book_availability': book_availability,
            "book_description": str(book_desc),
            "book_img_link": book_img_full_link,
        }
    # print(single_book_infos)
    return single_book_infos


def slugify(s):
    s = s.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_-]+', '-', s)
    s = re.sub(r'^-+|-+$', '', s)
    return s


def transform_single_book_data(data):
    """Fonction permettant de nettoyer les données d'un produit d'un dictionnaire
    avant de les insérer dans le fichier csv

    Arguments:
        data {dict} -- dictionnaire contenant les données du produit

    Returns:
        dict -- dictionnaire contenant les données du produit nettoyées
    """

    rating_dict = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, "Five": 5}

    # nettoyage des données
    data['book_rating'] = rating_dict[data['book_rating']]
    # conversion "book_price" en numérique et suppression des caractères spéciaux "Â" et "£"

    data['book_price'] = float(
        data['book_price'].replace('Â', '').replace('£', ''))
    #data['price_exc_tax'] = float(data['price_exc_tax'].replace('Â', '').replace('£', ''))
    #data['tax'] = float(data['tax'].replace('Â', '').replace('£', ''))

    # extraction des nombres dans book_availability  et conversion en numérique
    data['book_availability'] = int(
        re.findall(r'\d+', data['book_availability'])[0])

    # conversion de la colonne "book_category" en slug
    data['book_category'] = slugify(data['book_category'])

    # conversion de la colonne "book_title" en slug
    data['book_title'] = slugify(data['book_title'])

    return data


@timer
def get_category_links(url):
    """Fonction permettant de récupérer les liens des catégories

    Arguments:
        url {string} -- url de la page à traiter

    Returns:
        list -- liste des liens des catégories
    """

    soup = get_page_content(url)

    if soup is None:
        return None
    else:
        category_links = []
        category_links_extracted = soup.find_all(
            "ul", class_="nav nav-list")[0].findAll('a')[1:]
        for link in category_links_extracted:
            category_links.append(base_url + link['href'])

    return category_links


@timer
def get_single_category_book_links(category_url):
    """Fonction permettant de récupérer les liens des livres d'une catégorie donnée

    Arguments:
        category_url {string} -- url de la catégorie à traiter

        Returns:
            list -- liste des liens des livres de la catégorie donnée      
    """

    soup = get_page_content(category_url)
    categorie_name = category_url.split('/')[6]
    next_btn = soup.findAll('li', class_="next")

    category_book_links = []

    if len(next_btn) == 0:
        soup = get_page_content(category_url)
        articles = soup.findAll('article', class_="product_pod")
        for article in articles:
            book_extracted_link = article.find('h3').a["href"]
            book_link = base_book_url + book_extracted_link.lstrip("../../../")
            category_book_links.append(book_link)
    else:
        num_pages = int(soup.findAll('li', class_="current")
                        [0].text.strip(" \n ")[-1])
        for i in range(1, num_pages+1):
            next_btn_url = next_btn[0].a["href"]
            page_url = base_page_url + categorie_name + "/page-"+str(i)+".html"
            soup = get_page_content(url=page_url)
            articles = soup.findAll('article', class_="product_pod")
            for article in articles:
                book_extracted_link = article.find('h3').a["href"]
                book_link = base_book_url + \
                    book_extracted_link.lstrip("../../../")
                category_book_links.append(book_link)

    return category_book_links


def get_single_category_book_datas(category_url):
    """Fonction permettant de récupérer les données des livres d'une catégorie donnée

    Arguments:
        category_url {string} -- url de la catégorie à traiter

    Returns:
        list -- liste des données des livres de la catégorie donnée
    """
    category_name = category_url.split('/')[6]
    category_book_links = get_single_category_book_links(category_url)

    category_book_data = []
    for link in category_book_links:
        extracted_books_datas = extract_single_book_content(link)
        transformed_books_datas = transform_single_book_data(
            extracted_books_datas)
        category_book_data.append(transformed_books_datas)

    return category_book_data


def save_books_infos_to_csv(list_dict_datas, file_name):
    """Fonction permettant de sauvegarder les données d'une liste de dictionnaire dans un fichier csv

    Arguments:
        list_dict_datas {list} -- liste de dictionnaire contenant les données du produit
        csv_file_name {string} -- nom du fichier csv
    """
    columns_names = list_dict_datas[0].keys()

    csv_file_name = file_name + ".csv"
    try:
        with open("datas/csv_files/"+csv_file_name, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = columns_names

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(list_dict_datas)

    except IOError:
        print("I/O error")


@timer
def get_and_save_all_categories_books_datas():
    """Fonction permettant de récupérer et de sauvegarder les données des livres de toutes les catégories
    """
    t1 = time.time()
    category_links = get_category_links(home_url)
    for category_url in category_links:
        category_name = category_url.split('/')[6].split('_')[0]
        print("Traitement de la catégorie :", category_name + "...")
        get_and_save_single_category_book_datas(category_url)
    t2 = time.time()

    return print(f"Temps d'exécution total : {t2-t1} secondes")


@timer
def get_and_save_all_books_datas(file_name="__all_books_datas"):
    """Fonction permettant de récupérer et de sauvegarder données de tous les livres
    """

    t1 = time.time()
    category_links = get_category_links(home_url)

    all_books_datas = []
    for category_url in category_links:
        category_name = category_url.split('/')[6].split('_')[0]
        print("Traitement de la catégorie :", category_name + "...")
        category_book_datas = get_single_category_book_datas(category_url)
        all_books_datas.extend(category_book_datas)
        print("Nombre de livres traités :", len(all_books_datas))
        print("Sauvegarde des données de la catégorie :", category_name + "...")

    save_books_infos_to_csv(all_books_datas, file_name)
    t2 = time.time()

    print("Nombre total de livres traités :", len(all_books_datas))
    print("\nTemps d'exécution :", t2-t1)

    df = pd.read_csv("./datas/csv_files/"+file_name+".csv", sep=',')

    return all_books_datas, df


def save_book_image(image_url, image_name, image_category):
    """Fonction permettant de sauvegarder une image à partir de son url

    Arguments:
        image_url {string} -- url de l'image
        image_name {string} -- nom de l'image
        image_category {string} -- catégorie de l'image
    """
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            with open("datas/images/"+image_category+"/"+image_name+".jpg", 'wb') as f:
                f.write(response.content)
    except:
        print("Erreur lors du téléchargement de l'image :", image_name)


def create_category_folder(category):
    """Fonction permettant de créer un dossier de catégorie s'il n'existe pas

    Arguments:
        category {string} -- nom de la catégorie
    """
    if not os.path.exists("datas/images/" + category):
        os.mkdir("datas/images/" + category)

@timer
def save_book_images_by_category_in_subfolder(df):
    """Fonction permettant de sauvegarder les images des livres à partir de leur url obtenu du dataframe par catégorie dans un dossier par catégorie

    Arguments:
        df {dataframe} -- dataframe contenant les données des livres
    """
    for category in df.book_category.unique():
        print("Traitement de la catégorie :", category + "...")
        category_df = df[df.book_category == category]
        category_df = category_df.reset_index(drop=True)
        create_category_folder(category)

        for index, row in category_df.iterrows():
            print("\tTraitement du livre :", row.book_title)
            image_url = row.book_img_link
            image_name = row.book_title
            image_category = row.book_category
            save_book_image(image_url, image_name, image_category)
            #print("Livre traité :", row.book_title)
            # print("\n")
        print("Catégorie traitée :", category)
        print("\n")

@timer
def main():

    # Récupération des liens des catégories
    print("\n")
    category_links = get_category_links(home_url)
    print("Number of categories :", len(category_links))

    print("\n")
    # Recupération et sauvegarde des données de tous les livres
    print("Initialisation du processus d'extraction...")
    books_data_dict, books_data_df = get_and_save_all_books_datas()

    #  Recupération et sauvegarde des données de tous les livres par catégorie
    # get_and_save_all_categories_books_datas()

    print("\n")
    # Sauvegarde des images des livres
    print("Initialisation du processus de sauvegarde d'images ...")
    save_book_images_by_category_in_subfolder(books_data_df)


if __name__ == "__main__":
    timer(main())
