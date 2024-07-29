import requests
from bs4 import BeautifulSoup
import re

# def Scrape(site):
#     if not re.match(r'^\w+://', site):
#         site = 'http://' + site
#     response = requests.get(site)
#     soup = BeautifulSoup(response.text, 'html.parser').get_text()
#     WordsArray = [word.strip() for word in soup.split() if word.strip()]
#     OnionLinks = [word for word in WordsArray if re.search(r'(https?://.*?\.onion)', word)]
#     OnionLinks = [("http://" if "http://" in url else "https://") + url.split("://")[1].split("/")[0] for url in OnionLinks]
#     return OnionLinks

def Scrape(site):
    if not re.match(r'^\w+://', site):
        site = 'http://' + site

    response = requests.get(site)
    soup = BeautifulSoup(response.text, 'html.parser').get_text()

    WordsArray = []
    for word in soup.split():
        stripped_word = word.strip()
        if stripped_word:
            WordsArray.append(stripped_word)

    OnionLinks = []
    for word in WordsArray:
        if re.search(r'(https?://.*?\.onion)', word):
            url = word
            if "http://" in url:
                newurl = "http://" + url.split("://")[1].split("/")[0].rstrip('/')
                OnionLinks.append(newurl)
            else:
                newurl = "https://" + url.split("://")[1].split("/")[0].rstrip('/')
                OnionLinks.append(newurl)

    return OnionLinks