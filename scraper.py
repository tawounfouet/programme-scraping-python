from contextlib import contextmanager
from bs4 import BeautifulSoup
import requests
import time

# Variables globales
base_url = "http://books.toscrape.com/"
home_url = "https://books.toscrape.com/index.html"
base_page_url = "http://books.toscrape.com/catalogue/category/books/"
base_book_url = "http://books.toscrape.com/catalogue/"
#base_category_url = "http://books.toscrape.com/"


# Fonction permettant de calculer le temps d'exécution d'une fonction
def timer(func):
    """
    Fonction permettant de calculer le temps d'exécution d'une fonction

    Arguments:
        func {function} -- fonction à traiter

    Returns:
        function -- fonction traitée
    """
    def wrapper(*args, **kwargs):

        # Start the stopwatch / counter
        t0_start = time.perf_counter()

        result = func(*args, **kwargs)

        # Stop the stopwatch / counter
        tf_stop = time.time()

        # Elapsed time
        elapsed_time = tf_stop - t0_start

        print("{} - Done in {:.2f}s".format(func.__name__, elapsed_time))
        print("Elapsed time:", tf_stop - t0_start, "seconds")
        return result
    return wrapper


# @contextmanager
# def timer(functitle):
#     t0 = time.time()
#     yield
#     print("{} - done in {:.0f}s".format(title, time.time() - t0))

# Fonction permettant de traiter les requêtes
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


# Url de la page de tes à traiter
sample_url = "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"

# Appel de la fonction
# get_single_book_content(sample_url)
# timer(get_single_book_content)(sample_url)


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


# Fonction permettant de recupérer les liens de livre d'une catégory donnée
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


# Url de la catégory à traiter
sample_category_url = "http://books.toscrape.com/catalogue/category/books/travel_2/index.html"


print("First module's name: {}".format(__name__))


def main():
    # Récupération du contenu de la page
    timer(get_single_book_content)(sample_url)

    # Récupération des liens des catégories
    print("\n")
    category_links = timer(get_category_links)(home_url)
    #category_links = get_category_links(home_url)
    print("Number of categories :", len(category_links))

    print("\n")
    # Récupération des liens des produits d'une catégorie
    import random
    random_category_url = random.choice(category_links)
    random_category_name = random_category_url.split('/')[6].split('_')[0]

    random_category_links = timer(
        get_single_category_book_links)(random_category_url)
    print(
        f"Number of books in the category {random_category_name} : { len(random_category_links)}")

    # Récupération des liens des produits
    #book_links = get_book_links(category_links)
    # print(book_links)

    # Récupération des données des produits
    #books_data = get_books_data(book_links)
    # print(books_data)


if __name__ == "__main__":
    main()
