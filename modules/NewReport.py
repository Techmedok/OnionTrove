import requests
from bs4 import BeautifulSoup
import re
import google.generativeai as genai
from pathlib import Path
from datetime import datetime
import json
import os
from urllib.parse import urljoin, urlparse
from PIL import Image
from PIL.ExifTags import TAGS
from time import time
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

VirusTotalApiKey = "7481355a86e3621c72a2a6b1fcb9f95eeb665bfea874c30ad38bb163dd2f0b7a"

def GeminiProGenAI(Prompt, RawText):
    genai.configure(api_key="AIzaSyDTZzFzmpgNeZhy-YSRiPqjx9tzwLpmE0I")
    safety_settings = [{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_HATE_SPEECH","threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}]
    model = genai.GenerativeModel(model_name="gemini-pro", generation_config={"temperature": 0.9, "top_p": 1, "top_k": 1, "max_output_tokens": 2048}, safety_settings = safety_settings)
    convo = model.start_chat()
    Query = Prompt + " " + RawText
    response = convo.send_message(Query).text.strip()
    return response

def GeminiVisionPro(Query, ImagePath):
    genai.configure(api_key="AIzaSyDTZzFzmpgNeZhy-YSRiPqjx9tzwLpmE0I")
    generation_config = {"temperature": 1, "top_p": 1, "top_k": 32, "max_output_tokens": 4096}
    safety_settings = [{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_HATE_SPEECH","threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}]
    model = genai.GenerativeModel(model_name="gemini-1.0-pro-vision-latest", generation_config=generation_config, safety_settings=safety_settings)
    image_parts = [{"mime_type": "image/jpeg", "data": Path(ImagePath).read_bytes()}]
    prompt_parts = [Query, image_parts[0]]
    response = model.generate_content(prompt_parts).text.strip()
    return response

def GetTimestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def GetURL(url):
    pattern = r"(?<=\/\/)(.*?)(?=\.onion)"
    match = re.search(pattern, url)
    if match:
        name = match.group(0)
    if name.startswith("www."):
        name = name[4:]
    else:
        name = name
    return name  

def GetTorSiteData(url, OnionName,TorSession):
    try:
        response = TorSession.get(url)
        if response:
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string

            text = soup.get_text()
            rawtext = '\n'.join(line for line in text.splitlines() if line.strip())

            soupc = BeautifulSoup(response.content, 'html.parser')
            links = []
            for link in soupc.find_all("a"):
                href = link.get("href")
                if href:
                    links.append(href)
            for i in range(len(links)):
                if OnionName not in links[i]:
                    links[i] = "http://"+ OnionName + "/" + links[i]
            links = set(links)

            if not os.path.exists("static/" + OnionName):
                os.makedirs("static/" + OnionName)
            img_tags = soup.find_all('img')
            counter = 1
            imgnames=[]
            for img_tag in img_tags:
                img_src = img_tag.get('src')
                img_src = urljoin(url, img_src)
                if "logo" in os.path.basename(urlparse(img_src).path.lower()):
                    img_name = "logo.jpg"
                    imgnames.append(img_name)
                else:
                    img_name = f"{counter}.jpg"
                    imgnames.append(img_name)
                    counter += 1
                img_path = os.path.join("static/" + OnionName, img_name)
                try:
                    response = TorSession.get(img_src)
                    if response:
                        with open(img_path, 'wb') as img_file:
                            img_file.write(response.content)
                except requests.RequestException as e:
                    print(f"Error downloading image: {e}")
            return title, rawtext, links, imgnames
    except requests.RequestException as e:
        print(f"Error accessing the URL: {e}")

def GenerateSummary(RawText):
    Prompt = "Summarize the below context in an elaborate way: "
    summary = GeminiProGenAI(Prompt, RawText)
    return summary

def GenerateDetailedText(RawText):
    Prompt = "Generate a detailed context of the particular site based on the site content: "
    summary = GeminiProGenAI(Prompt, RawText)
    return summary

def GetCategoryTags(RawText):
    try:
        prompt = "Generate Category Tags based on the intended context for the below Site Data and return as Python List enclosed within Square Brackets: \n"
        response = GeminiProGenAI(prompt, RawText)
        jsonstring = response.replace("'", "\"")
        tags = json.loads(jsonstring)
        return tags
    except json.JSONDecodeError:
        GetCategoryTags(RawText)

def GetLegalOrIllegal(RawText):
    # prompt = "Using below context tell me it is illegal or legal stuff. Is this site legal? Your answer should be either True or False: \n"
    # output = GeminiProGenAI(prompt, RawText).lower()
    # if output == "true":
    #     return "Legal"
    # else:
    #     return "Illegal"
    return "Illegal"

def GenerateImageCaptions(OnionName, Images):
    Query = "Describe the image and Identify the Subject."
    ImageCaptions = []
    for Image in Images:
        ImagePath = "./static/" + OnionName + "/" + Image
        result = GeminiVisionPro(Query, ImagePath)
        ImageCaptions.append(result)
    return ImageCaptions

def GetOCR(OnionName, Images):
    Query = "Find for text in the image and return output as Single String. Return blank string if no text is found."
    OCRText = []
    for Image in Images:
        ImagePath = "./static/" + OnionName + "/" + Image
        result = GeminiVisionPro(Query, ImagePath)
        OCRText.append(result)
    return OCRText

def GetImageEXIF(OnionName, Images):
    EXIFdata = []
    for img in Images:
      try:
        ImagePath = "./static/" + OnionName + "/" + img
        imgo = Image.open(ImagePath)
        exif_data = imgo.getexif()
        if exif_data:
          exif_dict = {TAGS.get(key, key): value for key, value in exif_data.items() if value is not None}
          EXIFdata.append(json.dumps(exif_dict))
        else:
          EXIFdata.append("")
      except (IOError, FileNotFoundError):
        print(f"Error: Couldn't open image file: {img}")
    return EXIFdata

def GetContactData(RawText):
    EmailPattern = r'\b[A-Za-z0-9._%+-]+(?:@|\[@\]|\[at\])(?:[A-Za-z0-9.-]+)(?:\.|\[\.\]|\[dot\])' \
                    r'[A-Z|a-z]{2,}\b'
    Emails = re.findall(EmailPattern, RawText)
    return Emails

def IsMaliciousSite(url, VirusTotalApiKey):
    api_url = "https://www.virustotal.com/vtapi/v2/url/report"
    params = {'apikey': VirusTotalApiKey, 'resource': url}
    response = requests.get(api_url, params=params)
    result = response.json()

    if result['response_code'] == 1 and result['positives'] > 0:
        return "True", result['permalink']
    else:
        return "False", result['permalink']

def IdentifyCrypto(Address):
    if re.match("^(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}$", Address):
        return "Bitcoin"
    elif re.match("^0x[a-fA-F0-9]{40}$", Address): 
        return "Ethereum"
    elif re.match("^4[a-zA-Z0-9]{94}$", Address):
        return "Monero"
    else:
        return False
    
def FindCryptoAddress(RawText):
    Words = RawText.split()
    Words = [word for word in Words if len(word) > 20]
    for Word in Words:
        Coin = IdentifyCrypto(Word)
        if Coin:
            return Coin, Word
    return False, False

def GetTransactionsData(CryptoCoin, Address):
    if CryptoCoin == "Bitcoin":
        Transactions, Balance = GetBTCData(Address)
    elif CryptoCoin == "Ethereum":
        Transactions, Balance = GetETHData(Address)
    elif CryptoCoin == "Monero":
        Transactions = "Private Crypto Currency"
        Balance = "Private Crypto Currency"
    elif CryptoCoin == "Unknown Crypto":
        Transactions = ""
        Balance = ""
    return Transactions, Balance

def GetETHData(Address):
    TransactionsDataURL = f"https://api.etherscan.io/api?module=account&action=txlist&address={Address}&sort=desc&offset=10&page=1"
    response = requests.get(TransactionsDataURL)
    data = response.json()
    TransactionsList = data["result"]
    Transactions = []
    for Transaction in TransactionsList:
        TransactionsData = {
            'Hash': Transaction['hash'],
            'Time': datetime.utcfromtimestamp(int(Transaction['timeStamp'])).strftime("%Y-%m-%d %H:%M:%S UTC"),
            'FromAddress': Transaction['from'],
            'ToAddress': Transaction['to'],
            'Value': str(float(Transaction['value']) / 10**18) + " ETH"
        }
        Transactions.append(TransactionsData)
    time.sleep(5)
    BalanceURL = f"https://api.etherscan.io/api?module=account&action=balance&address={Address}"
    response = requests.get(BalanceURL).json()
    Balance = str(float(response["result"])/10**18) + " ETH"
    return Transactions, Balance

def GetBTCData(Address):
    TransactionsDataURL = f"https://blockstream.info/api/address/{Address}/txs"
    response = requests.get(TransactionsDataURL)
    TransactionsList = response.json()[:10]
    Transactions = []
    for Transaction in TransactionsList:
        TransactionsData = {
            'Hash': Transaction['txid'],
            'Time': datetime.utcfromtimestamp(int(Transaction['status']['block_time'])).strftime("%Y-%m-%d %H:%M:%S UTC") if "status" in Transaction and "block_time" in Transaction["status"] else "",
            'FromAddress': Transaction['vin'][0]['prevout']['scriptpubkey_address'],
            'ToAddress': Transaction['vout'][0]['scriptpubkey_address'],
            'Value': str(float(Transaction['vin'][0]['prevout']['value']) / 10**8) + " BTC"
        }
        Transactions.append(TransactionsData)
    BalanceURL = f"https://blockstream.info/api/address/{Address}"
    response = requests.get(BalanceURL).json()
    Balance = str((response['chain_stats']['funded_txo_sum'] - response['chain_stats']['spent_txo_sum'])/10**8) + " BTC"
    return Transactions, Balance

def GetScreenShots(onionname, url, links):
    try:
        links = list(links)
        links.insert(0, url)  # Add the initial URL to the beginning of the list

        count = 1
        path_list = []  # Store paths relative to 'static' directory

        # Ensure the screenshot directory exists
        os.makedirs("static/" + onionname + "/screenshots", exist_ok=True)

        # Use a single Chrome driver instance for efficiency
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--force-device-scale-factor=2')
        options.add_argument('--proxy-server=socks5://localhost:9050')
        options.add_argument('--remote-debugging-port=9222')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_window_size(1920, 1080)

        for link in links:
            driver.get(link)
            height = driver.execute_script('return document.documentElement.scrollHeight')
            width = driver.execute_script('return document.documentElement.scrollWidth')
            driver.set_window_size(width, height)

            path = "static/" + onionname + "/screenshots/" + str(count) + ".png"
            driver.save_screenshot(path)
            path_list.append(onionname + "/screenshots/" + str(count) + ".png")  # Store relative path
            count += 1

        driver.quit()  # Close the driver after all screenshots are taken

        return path_list

    except Exception as e:
        print(f"Error: {e}")
        return []  # Return an empty list in case of errors

def Main(url, TorSession):
    OnionName = GetURL(url) + ".onion"
    Timestamp = GetTimestamp()
    Title, RawText, Links, Images = GetTorSiteData(url, OnionName, TorSession)
    ScreenShots = GetScreenShots(OnionName, url, Links)

    functions_and_args = [
        (GenerateSummary, (RawText,)), #Checked
        (GenerateDetailedText, (RawText,)), #Checked
        (GetCategoryTags, (RawText,)), #Checked
        (GetLegalOrIllegal, (RawText,)), #Checked
        (GenerateImageCaptions, (OnionName, Images)), #Checked
        (GetOCR, (OnionName, Images)), #Checked
        (GetImageEXIF, (OnionName, Images)), #Checked
    ]

    Result = {}

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(func, *args): (func.__name__, args) for func, args in functions_and_args}
        for future in concurrent.futures.as_completed(futures):
            func_name, args = futures[future]
            try:
                result = future.result()
                Result[func_name] = result
            except Exception as e:
                Result[func_name] = str(e)

    Summary = Result["GenerateSummary"]
    DetailedText = Result["GenerateDetailedText"]
    CategoryTags = Result["GetCategoryTags"]
    LegalOrIllegal = Result["GetLegalOrIllegal"]
    ImageCaptions = Result["GenerateImageCaptions"]
    ImageText = Result["GetOCR"]
    EXIFData = Result["GetImageEXIF"]

    ContactData = GetContactData(RawText)
    CryptoCoin, Address = FindCryptoAddress(RawText)
    if CryptoCoin:
        Transactions, Balance = GetTransactionsData(CryptoCoin, Address)
    else:
        Transactions = None
        Balance = None
    IsMalicious, VirusTotalLink = IsMaliciousSite(url, VirusTotalApiKey)

    data = {
        "URL": OnionName,
        "Title": Title,
        "Time": Timestamp,
        "Tags": CategoryTags,
        "Legal": LegalOrIllegal,
        "RawText": RawText,
        "Summary": Summary,
        "DetailedText": DetailedText,
        "Links": list(Links),
        "Images": Images,
        "ScreenShots": ScreenShots,
        "ImageCaptions": ImageCaptions,
        "ImageText": ImageText,
        "EXIFData": EXIFData,
        "ContactData": ContactData,
        "CryptoCoin": CryptoCoin,
        "Address": Address,
        "Transactions": Transactions,
        "Balance": Balance,
        "IsMalicious": IsMalicious,
        "VirusTotalLink": VirusTotalLink,
    }

    return data