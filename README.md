# Programme Web Scraping 
Programme développé en python permettant d’automatiser l’extraction des informations tarifaires d’une librairie en ligne et d’effectuer le suivi le prix des livres de cette librairie. 

## Description
Ce code permet de scraper les données des livres sur le site books.toscrape.com. Les données sont stockées dans un fichier CSV.


## Prérequis : Mise en Place de l'environnement de développement 
Avant de pouvoir exécuter le code, vous devez installer les librairies nécessaires. Les librairies sont listées dans le fichier requirements.txt. Vous pouvez les installer en exécutant la commande suivante :

```bash
pip install -r requirements.txt
```

Il est recommandé d'utiliser un environnement virtuel pour l'installation de ces librairies. Vous pouvez créer un environnement virtuel en utilisant virtualenv. Si vous n'avez pas encore installé virtualenv, vous pouvez l'installer en utilisant la commande suivante :
    
```bash 
pip install virtualenv
```

Vous pouvez ensuite créer un environnement virtuel en utilisant la commande suivante :

```bash
virtualenv env
```

Ceci va créer un environnement virtuel nommé venv dans le répertoire courant. Pour activer l'environnement virtuel, exécutez la commande suivante :

```bash
source env/bin/activate
```

## Exécution du code
Une fois que vous avez installé les librairies nécessaires et créé un environnement virtuel, vous pouvez exécuter le code en utilisant la commande suivante :
    
```bash  
python books_scraper.py
```




Assurez-vous que vous êtes bien dans l'environnement virtuel avant d'exécuter le code. Si vous avez activé l'environnement virtuel en utilisant la commande source venv/bin/activate, le nom de l'environnement virtuel devrait s'afficher dans votre terminal. Par exemple, si vous avez créé un environnement virtuel nommé venv, le nom de l'environnement virtuel devrait s'afficher comme ceci :

```bash
(venv) $
```
