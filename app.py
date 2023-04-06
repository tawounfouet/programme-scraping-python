from contextlib import contextmanager
from bs4 import BeautifulSoup
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



# Fonction permettant de calculer le temps d'exécution d'une fonction
# Fonction permettant de chronométrer l'exécution d'une fonction
def timer(func):
    """Fonction permettant de chronométrer l'exécution d'une fonction

    Arguments:
        func {function} -- fonction à chronométrer

    Returns:
        function -- fonction chronométrée
    """
    def wrapper(*args, **kwargs):
        #start = time.time()
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"Execution time : {end - start} seconds")
        return result
    return wrapper



# Fonction permettant de traiter les requêtes et recupérer le contenu d'une page donnée
def get_page_content(url, parser="lxml"):
    """
    Fonction permettant de traiter les requêtes et recupérer le contenu d'une page donnée

    Arguments:
        url: url de la page à traiter
        parser: parser à utiliser pour traiter le contenu de la page

    Returns:
        BeautifulSoup: objet BeautifulSoup contenant le contenu de la page
    """
    response = requests.get(url)

    if not response.ok:
        print("Error: ", response.status_code)
        return None
    else:
        response.encoding = "utf-8"
        content = response.content
        extracted_soup = BeautifulSoup(content, parser)
        return extracted_soup


# Fonction qui récupère le contenu d'une page
def get_single_book_content(url):
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


# url de la page de tes à traiter
sample_url = "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
single_book_datas = get_single_book_content(sample_url)
columns_names = single_book_datas.keys()



# Fonction permettant de récupérer les liens des catégories
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


# Fonction permettant de recupérer les liens des produits d'une catégory donnée
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




# Fontion permettant de récupérer des données des livres d'une catégorie
def get_single_category_book_datas(sample_category_url):
    """Fonction permettant de récupérer les données des livres d'une catégorie donnée

    Arguments:
        sample_category_url {string} -- url de la catégorie à traiter

    Returns:
        list -- liste des données des livres de la catégorie donnée
    """
    category_name = sample_category_url.split('/')[6]
    category_book_links = get_single_category_book_links(sample_category_url)

    category_book_data = []
    for link in category_book_links:
        single_book_datas = get_single_book_content(link)
        category_book_data.append(single_book_datas)

    return category_book_data


# Fonction permettant de sauvegarder les données d'une liste de dictionnaire dans un fichier csv
def save_books_infos_to_csv(list_dict_datas, file_name):
    """Fonction permettant de sauvegarder les données d'une liste de dictionnaire dans un fichier csv

    Arguments:
        list_dict_datas {list} -- liste de dictionnaire contenant les données du produit
        csv_file_name {string} -- nom du fichier csv
    """

    csv_file_name = file_name + ".csv"
    try:
        with open("datas/"+csv_file_name, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = columns_names

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for book in list_dict_datas:
                writer.writerow(book)
    except IOError:
        print("I/O error")


# Fonction permettant de récupérer et de sauvegarder les données des livres d'une catégorie
def get_and_save_single_category_book_datas(category_url):
    """Fonction permettant de récupérer et de sauvegarder les données des livres d'une catégorie

    Arguments:
        sample_category_url {string} -- url de la catégorie à traiter
    """
    category_name = category_url.split('/')[6].split('_')[0]

    category_book_datas = get_single_category_book_datas(sample_category_url)
    save_books_infos_to_csv(category_book_datas, category_name)



# Fonction permettant de récupérer et de sauvegarder les données de tous les livres
def get_and_save_all_books_datas():
    """Fonction permettant de récupérer et de sauvegarder données de tous les livres
    """
    all_books_datas = []

    category_links = get_category_links(home_url)

    for category_url in category_links:
        category_name = category_url.split('/')[6].split('_')[0]
        print("Traitement de la catégorie :", category_name + "...")
        category_book_datas = get_single_category_book_datas(category_url)
        all_books_datas.extend(category_book_datas)
        print("Nombre de livres traités :", len(all_books_datas))
        #print("\n")

    save_books_infos_to_csv(all_books_datas, "__all_books_datas__")

    print("Nombre total de livres traités :", len(all_books_datas))

    return all_books_datas



import re
def slugify(s):
    s = s.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_-]+', '-', s)
    s = re.sub(r'^-+|-+$', '', s)
    return s


# Fonction permettant de lire et transformer les doneés des livres d'un fichier csv en dataframe
def transform_extract_datas(file_name):
    """Fonction permettant de transformer les données d'un fichier csv en dataframe

    Arguments:
        csv_file_name {string} -- nom du fichier csv

    Returns:
        dataframe -- dataframe contenant les données du fichier csv
    """
    csv_file_name = file_name + ".csv"

    df = pd.read_csv("datas/"+csv_file_name, sep=',')

    # Transformation des données
    # conversion de la colonne "book_price" en numérique
    df["book_price"] = df["book_price"].str.replace("£", "")
    #df["book_price"] = df["book_price"].astype(float)

    # conversion de la colonne "rating" en numérique
    rating_dict = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, "Five":5} 
    df['book_rating'] = df['book_rating'].map(rating_dict)


    #df['book_availability'] =  df['book_availability'].apply(lambda x: x.split(" ")[2].strip("("))
    #df['book_availability'] = df['book_availability'].astype(int)

    # conversion de la colonne "book_category" en slug
    df['book_category'] = df['book_category'].apply(lambda s: slugify(s))

    # conversion de la colonne "book_title" en slug
    df['book_title'] = df['book_title'].apply(lambda s: slugify(s))

    # sauvegarde du dataframe dans un fichier csv
    df.to_csv("datas/"+file_name+"_transformed.csv", index=False)

    return df


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


# Fonction permettant de créer un dossier de catégorie s'il n'existe pas
def create_category_folder(category):
    """Fonction permettant de créer un dossier de catégorie s'il n'existe pas

    Arguments:
        category {string} -- nom de la catégorie
    """
    if not os.path.exists("datas/images/"+ category): 
        os.mkdir("datas/images/"+ category)



# Fonction permettant de sauvegarder les images des livres à partir de leur url obtenu du dataframe par catégorie dans un dossier par catégorie
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
            print("Traitement du livre :", row.book_title)
            image_url = row.book_img_link
            image_name = row.book_title
            image_category = row.book_category
            save_book_image(image_url, image_name, image_category)
            #print("Livre traité :", row.book_title)
            #print("\n")
        print("Catégorie traitée :", category)
        print("\n")


def main():

    # Récupération des liens des catégories
    print("\n")
    category_links = timer(get_category_links)(home_url)
    print("Number of categories :", len(category_links))

    print("\n")
    # Phase 1 du processus ETL - Etract 
    # Recupération et sauvegarde des données de tous les livres
    #print("Initialisation du processus d'extraction...")
    #books_datas = timer(get_and_save_all_books_datas())

    print("\n")
    # Phase 2 du processus ETL - Transform
    # Transformation des données
    print("Initialisation du processus de traitement ...")
    book_df = timer(transform_extract_datas)("__all_books_datas__")

    print("\n")
    # Phase 3 du processus ETL - Load
    # Sauvegarde des images des livres
    print("Initialisation du processus de sauvegarde d'images ...")
    timer(save_book_images_by_category_in_subfolder)(book_df)
    
if __name__ == "__main__":
    timer(main())