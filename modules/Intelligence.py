import os
import re
from hugchat import hugchat
from hugchat.login import Login
import subprocess
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import pytesseract
from PIL import Image
from PIL.ExifTags import TAGS
import cv2
from selenium import webdriver
import json
from datetime import datetime
import time
from AddDB import AddDB
from selenium import *

VirusTotalApiKey = "7481355a86e3621c72a2a6b1fcb9f95eeb665bfea874c30ad38bb163dd2f0b7a"
     
headers = {"Authorization": "Bearer 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"}

class TorSession:
    def __init__(self):
        self.tor_process = subprocess.Popen(["C:\\Tor Browser\\Browser\\TorBrowser\\Tor\\tor.exe"])
        self.proxies = {'http': 'socks5h://127.0.0.1:9050', 'https': 'socks5h://127.0.0.1:9050'}
        self.session = requests.Session()
    def get(self, url):
        try:
            response = self.session.get(url, proxies=self.proxies)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            print(f"Error accessing the URL: {e}")
            return None
    def terminate(self):
        self.tor_process.terminate()

def IsSiteUp(url, TorSession):
    try:
        response = TorSession.get(url)
        if response.status_code == 200:
            return True
        else:
            return False
    except requests.RequestException as e:
        return False

def MixtralAI(prompt, content):
    cookie_path_dir = "./cookies_snapshot"
    sign = Login("nitishkumar.blog@gmail.com", None)
    cookies = sign.loadCookiesFromDir(cookie_path_dir)
    chatbot = hugchat.ChatBot(cookies=cookies.get_dict())
    query = prompt + content
    query_result = chatbot.query(query)
    return str(query_result)

# cookie_path_dir = "./cookies_snapshot"
# sign = Login("nitishkumar.blog@gmail.com", None)
# cookies = sign.loadCookiesFromDir(cookie_path_dir)
# chatbot = hugchat.ChatBot(cookies=cookies.get_dict())
# query_result = chatbot.query("Hi!")
# print(query_result) # or query_result.text or query_result["text"]

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

def GetTitle(url, TorSession):
    try:
        response = TorSession.get(url)
        if response:
            soup = BeautifulSoup(response.content, 'html.parser')
            title = soup.title.string
            return title
    except requests.RequestException as e:
        print(f"Error accessing the URL: {e}")
    return "Title retrieval failed."

def GetRawText(url, TorSession):
    try:
        response = TorSession.get(url)
        if response:
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text()
            rawtext = '\n'.join(line for line in text.splitlines() if line.strip())
            return rawtext
    except requests.RequestException as e:
        print(f"Error accessing the URL: {e}")
    return "Text retrieval failed."

def GenerateSummary(RawText):
    prompt = "Summarize the below context in an elaborate way: "
    summary = MixtralAI(prompt, RawText)
    return summary

def GenerateDetailedText(RawText):
    prompt = "Generate a detailed context of the particular site based on the site content: "
    summary = MixtralAI(prompt, RawText)
    return summary

def GetCategoryTags(RawText):
    prompt = "Generate Category Tags based on the intended context for the below Site Data and return as array. Give any array which you know:"
    response = MixtralAI(prompt, RawText)

    pattern = r'\* (["\'])(.*?)\1'
    TagsList = re.findall(pattern, response)
    TagsList = [match[1] for match in TagsList] if TagsList else []

    pattern = r"\[([^\]]*)\]"
    TagsArrayMatch = re.search(pattern, response)
    TagsArray = TagsArrayMatch.group(1).split(', ') if TagsArrayMatch else []
    TagsArray = [re.sub(r'["\']', '', element) for element in TagsArray]

    Tags = list(set(TagsList + TagsArray))
    return Tags

def GetLegalOrIllegal(RawText):
    prompt = "Using below context tell me it is illegal or legal stuff. Return your answer in json format {'legal': '(True/Flase)', 'illegal': '(True/Flase)'} : "
    output = MixtralAI(prompt, RawText)
    json_start = output.find('{')
    json_end = output.rfind('}') + 1
    match = output[json_start:json_end]
    match = match.replace("'", "\"")
    try:
        json_data = json.loads(match)
        found_key = next((key for key, value in json_data.items() if value is True), None)
        if found_key is not None:
            return found_key
        else:
            return ""
    except json.JSONDecodeError:
        return ""
    
def GetLinks(OnionName, url, TorSession):
    try:
        response = TorSession.get(url)
        if response:
            soup = BeautifulSoup(response.content, 'html.parser')
            links = []
            for link in soup.find_all("a"):
                href = link.get("href")
                if href:
                    links.append(href)
            for i in range(len(links)):
                if OnionName not in links[i]:
                    links[i] = "http://"+ OnionName + "/" + links[i]
            return set(links)
    except requests.RequestException as e:
        print(f"Error accessing the URL: {e}")
    return "Text retrieval failed."

def GetImages(url, onionname, TorSession):
    try:
        response = TorSession.get(url)
        if response:
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            if not os.path.exists("static/" + onionname):
                os.makedirs("static/" + onionname)
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
                img_path = os.path.join("static/" + onionname, img_name)
                try:
                    response = TorSession.get(img_src)
                    if response:
                        with open(img_path, 'wb') as img_file:
                            img_file.write(response.content)
                        print(f"Downloaded: {img_path}")
                except requests.RequestException as e:
                    print(f"Error downloading image: {e}")
            return imgnames
    except requests.RequestException as e:
        print(f"Error accessing the URL: {e}")
    return "Image download failed."

def GenerateImageCaptions(OnionName, Images):
    try:
        ImageCaptions=[]
        for image in Images:
            loc = "./static/" + OnionName + "/" + image
            with open(loc, "rb") as f:
                data = f.read()
            response = requests.post("https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large", headers=headers, data=data)
            ImageCaptions.append(response.json()[0]["generated_text"])
        return ImageCaptions
    except requests.RequestException as e:
        print(f"Error: {e}")
    return "Image Captioning failed."

def GetOCR(Images, OnionName):
    ocrtext=[]
    for img in Images:
        image = cv2.imread("./static/" + OnionName + "/" + img)
        upscale_factor = 8
        enhanced_image_cv2 = cv2.addWeighted(image, 1.2, image, 0, 30)
        upscaled_enhanced_image_cv2 = cv2.resize(enhanced_image_cv2, (image.shape[1]*upscale_factor, image.shape[0]*upscale_factor), interpolation=cv2.INTER_LINEAR)
        cv2.imwrite('EnhancedImage.jpg', upscaled_enhanced_image_cv2) 
        os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata' #remove on prod
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe' #remove on prod
        image = Image.open("EnhancedImage.jpg")
        image = image.convert('L')
        text = pytesseract.image_to_string(image)
        text = [line.strip() for line in text.split('\n') if line.strip()]
        result = '\n'.join(text)
        os.remove("EnhancedImage.jpg")
        ocrtext.append(result)
    return ocrtext


# # Set the path to the Tesseract executable (on Windows, it might not be necessary)
# pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

# # Open an image using PIL (Python Imaging Library)
# image_path = 'path/to/your/image.png'
# img = Image.open(image_path)

# # Use pytesseract to do OCR on the image
# text = pytesseract.image_to_string(img)

# # Print the extracted text
# print(text)


def GetImageEXIF(Images, OnionName):
    EXIFdata = []
    for img in Images:
        try:
            with Image.open("./static/" + OnionName + "/" + img) as img:
                exif = img.getexif()
                exif_data = {**{TAGS.get(tag_id, tag_id): value for tag_id, value in exif.items()}} if exif else {}
            EXIFdata.append(exif_data)
        except Exception as e:
            print(f"Error processing image '{img}': {e}")
            EXIFdata.append(None)
    return EXIFdata

def GetScreenShots(onionname, url, Links):
    try:
        Links = list(Links)
        Links.insert(0, url)
        count=1
        Path = []
        if not os.path.exists("static/" + onionname + "/screenshots"):
            os.makedirs("static/" + onionname + "/screenshots")
        for Link in Links:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--force-device-scale-factor=2')
            options.add_argument('--proxy-server=socks5://localhost:9050')
            options.add_argument('--remote-debugging-port=9222')
            options.add_experimental_option('excludeSwitches', ['enable-automation'])
            options.add_experimental_option('useAutomationExtension', False)
            driver = webdriver.Chrome(options=options)
            driver.set_window_size(1920, 1080)
            driver.get(Link)
            height = driver.execute_script('return document.documentElement.scrollHeight')
            width  = driver.execute_script('return document.documentElement.scrollWidth')
            driver.set_window_size(width, height)
            path = "static/" + onionname + "/screenshots/" + str(count) + ".png"
            driver.save_screenshot(path)
            driver.quit()
            patha = onionname + "/screenshots/" + str(count) + ".png"
            Path.append(patha)
            count=count+1
        return Path
    except Exception as e:
        print(f"Error: {e}")

# def GetScreenShots(onionname, url):
#     try:
#         options = webdriver.ChromeOptions()
#         options.add_argument('--headless')
#         options.add_argument('--force-device-scale-factor=2')
#         options.add_argument('--proxy-server=socks5://localhost:9050')
#         options.add_argument('--remote-debugging-port=9222')
#         options.add_experimental_option('excludeSwitches', ['enable-automation'])
#         options.add_experimental_option('useAutomationExtension', False)
#         driver = webdriver.Chrome(options=options)
#         driver.set_window_size(1920, 1080)
#         driver.get(url)
#         height = driver.execute_script('return document.documentElement.scrollHeight')
#         width  = driver.execute_script('return document.documentElement.scrollWidth')
#         driver.set_window_size(width, height)
#         path = "static/" + onionname + ".png"
#         driver.save_screenshot(path)
#         driver.quit()
#         return path
#     except Exception as e:
#         print(f"Error: {e}")
        
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

def GetTimestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart

# def Send(subject, body, to):
#     email = "oniontrove@techmedok.com"
#     password = "oniontrove123"
#     message = MIMEMultipart()
#     message["From"] = email
#     message["To"] = to
#     message["Subject"] = subject
#     message.attach(MIMEText(body, "plain"))
#     with smtplib.SMTP_SSL("smtp.yandex.com", 465) as server:
#         server.login(email, password)
#         server.sendmail(email, to, message.as_string())
#     return True


if __name__ == "__main__":
    # class TorSession:
    #     def __init__(self):
    #         self.tor_process = subprocess.Popen(["C:\\Tor Browser\\Browser\\TorBrowser\\Tor\\tor.exe"])
    #         self.proxies = {'http': 'socks5h://127.0.0.1:9050', 'https': 'socks5h://127.0.0.1:9050'}
    #         self.session = requests.Session()
    #     def get(self, url):
    #         try:
    #             response = self.session.get(url, proxies=self.proxies)
    #             response.raise_for_status()
    #             return response
    #         except requests.RequestException as e:
    #             print(f"Error accessing the URL: {e}")
    #             return None
    #     def terminate(self):
    #         self.tor_process.terminate()
            
    # url = "http://wbz2lrxhw4dd7h5t2wnoczmcz5snjpym4pr7dzjmah4vi6yywn37bdyd.onion/"
    url = "http://wbz2lrxhw4dd7h5t2wnoczmcz5snjpym4pr7dzjmah4vi6yywn37bdyd.onion/"
    TorSession = TorSession()


    OnionName = GetURL(url) + ".onion"
    Title = GetTitle(url, TorSession)
    RawText = GetRawText(url, TorSession)
    Summary = GenerateSummary(RawText)
    DetailedText = GenerateDetailedText(RawText)
    CategoryTags = GetCategoryTags(RawText)
    
    LegalOrIllegal = GetLegalOrIllegal(RawText)

    Links = GetLinks(OnionName, url, TorSession)
    Images = GetImages(url, OnionName, TorSession)

    ImageCaptions = GenerateImageCaptions(OnionName, Images)
    ImageText = GetOCR(Images, OnionName)

    EXIFData = GetImageEXIF(Images, OnionName)
    
    ScreenShots = GetScreenShots(OnionName, url, Links)
    ContactData = GetContactData(RawText)
    CryptoCoin, Address = FindCryptoAddress(RawText)
    if CryptoCoin:
        Transactions, Balance = GetTransactionsData(CryptoCoin, Address)
    else:
        Transactions = None
        Balance = None
    IsMalicious, VirusTotalLink = IsMaliciousSite(url, VirusTotalApiKey)

    for i in range(len(Images)):
        Images[i] = OnionName + "/" + Images[i]
    Summary = str(Summary)
    DetailedText = str(DetailedText)
    CategoryTags = json.dumps(CategoryTags)
    Links = json.dumps(list(Links))
    Images = json.dumps(Images)
    ImageCaptions = json.dumps(ImageCaptions)
    ImageText = json.dumps(ImageText)
    EXIFData = json.dumps(EXIFData)
    ScreenShots = json.dumps(ScreenShots)
    ContactData = json.dumps(ContactData)
    Transactions = json.dumps(Transactions)
    Timestamp = GetTimestamp()

    # AddDB(Timestamp, OnionName, Title, RawText, Summary, DetailedText, CategoryTags, LegalOrIllegal, Links, Images, ImageCaptions, ImageText, EXIFData, ScreenShots, ContactData, CryptoCoin, Address, Transactions, Balance, IsMalicious, VirusTotalLink)
    AddDB(Timestamp, OnionName, Title, RawText, Summary, DetailedText, CategoryTags, LegalOrIllegal, Links, Images, ImageCaptions, ImageText, EXIFData, ContactData, CryptoCoin, Address, Transactions, Balance, IsMalicious, VirusTotalLink)
    TorSession.terminate()
    # if LegalOrIllegal.lower() == "illegal":
    #     Send()

    # if LegalOrIllegal:
    #     Mail()
    # 5, 41, 218, 219