import requests
from bs4 import BeautifulSoup
import re

def Google(query, pages=1):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
    url_template = 'https://www.google.com/search?q={}&start={}'
    results = []
    for page in range(0, pages):
        start = page * 10
        url = url_template.format(query, start)
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.find_all('a', href=True)
        urls = [link['href'] for link in links]
        for link in urls:
            results.append(link)
    links=[]
    for link in results:
        match = re.search(r'&url=(.*?)&ved=', link)
        if match:
            links.append(match.group(1))
    return links

def Duckduckgo(query, pages=1):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
    url_template = 'https://duckduckgo.com/html/?q={}&page={}'
    results = []
    for page in range(1, pages+1):
        url = url_template.format(query, page)
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        for result in soup.find_all('div', {'class': 'result'}):
            link = result.find('a', href=True)
            title = result.find('a', {'class': 'result__url'}).text
            snippet = result.find('a', {'class': 'result__snippet'}).text
            if link and title and snippet:
                results.append(link['href'])
    return results

def Bing(query, pages=1):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
    url_template = 'https://www.bing.com/search?q={}&first={}'
    results = []
    for page in range(0, pages):
        url = url_template.format(query, page)
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        for result in soup.find_all('li', {'class': 'b_algo'}):
            link = result.find('a', href=True)
            title_elem = result.find('h2')
            title = title_elem.text.strip() if title_elem is not None else ''
            snippet_elem = result.find('div', {'class': 'b_caption'})
            snippet = snippet_elem.text.strip() if snippet_elem is not None else ''
            if link and title:
                results.append(link['href'])
    return results