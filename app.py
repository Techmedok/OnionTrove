from flask import Flask, render_template, redirect, url_for, flash, send_from_directory, request, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import psycopg2
import csv
import locale
from flask_cors import CORS #remove
from modules import Dork, OnionLinkScraper, OnionLinkCleaner, NewReport

import requests
import subprocess
from requests.exceptions import RequestException
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from flask_pymongo import PyMongo
import json

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

app = Flask(__name__)
CORS(app) #remove
app.config['SECRET_KEY'] = 'wTtKKRfdpTilHBY4tkBH'

app.config['MONGO_URI'] = 'mongodb://localhost:27017/OnionTrove'
mongo = PyMongo()
mongo.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

db_config = {
    'dbname': 'oniontrove',
    'user': 'oniontrove',
    'password': 'wTtKKRfdpTilHBY4tkBH',
    'host': '161.97.70.226',
}

connection = psycopg2.connect(**db_config)

class User(UserMixin):
    def __init__(self, user_id, username, password):
        self.id = user_id
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    with connection.cursor() as cursor:
        cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
        user_data = cursor.fetchone()
        if user_data:
            user = User(*user_data)
            return user
        else:
            return None
        
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
            user_data = cursor.fetchone()
        if user_data:
            user = User(user_data[0], user_data[1], user_data[2])
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/data')
@login_required
def chart_data():
    with connection.cursor() as cursor:
        cursor.execute("SELECT date, relays, bridges, torusers, onionlinks FROM tordata ORDER BY date DESC LIMIT 10")
        result = cursor.fetchall()
    categories = [row[0].strftime('%Y-%m-%d %H:%M:%S') for row in result]
    values = list(zip(*[[row[1], row[2], row[3], row[4]] for row in result]))
    chart_data = {
        'categories': categories,
        'values': values
    }
    return jsonify(chart_data)

@app.route('/dashboard')
@login_required
def dashboard():
    user = current_user.username
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM tordata ORDER BY date DESC LIMIT 1")
        result = list(cursor.fetchone())[1:] 
        locale.setlocale(locale.LC_NUMERIC, 'en_IN')
        result = [locale.format_string('%d', value, grouping=True) for value in result]
        locale.setlocale(locale.LC_NUMERIC, '')
    return render_template('dashboard.html', user=user, result=result)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
            existing_user = cursor.fetchone()
            if existing_user:
                flash('Username is already taken. Please choose a different one.', 'error')
            else:
                cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, password))
                connection.commit()
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
    return render_template('register.html', form=form)

# Keywords - done
@app.route('/keywords')
@login_required
def Keyword():
    with connection.cursor() as cursor:
        user = current_user.username
        query = "SELECT * FROM keywords"
        cursor.execute(query)
        keywords = cursor.fetchall()
        query = "SELECT * FROM count WHERE name='keywords'"
        cursor.execute(query)
        data = cursor.fetchone()
        val = data[1] if data else 0
    return render_template('keyword.html', user=user, keywords=keywords, val=val)

@app.route('/addkeyword', methods=['POST'])
@login_required
def AddKeyword():
    if request.method == 'POST':
        keyword = request.form.get('keyword')
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM keywords WHERE keywords = %s", (keyword,))
            result = cursor.fetchone()
            keyword_exists = result[0] > 0
            if not keyword_exists:
                query = "INSERT INTO keywords (keywords) VALUES (%s)"
                cursor.execute(query, (keyword,))
                connection.commit()
                flash("Keyword added successfully", "manual")
            else:
                flash("Keyword already exists", "manual")
    return redirect(url_for('Keyword'))

@app.route('/deletekeyword/<int:id>')
@login_required
def DeleteKeyword(id):
    with connection.cursor() as cursor:
        query = "DELETE FROM keywords WHERE id = %s"
        cursor.execute(query, (id,))
        # query = "SELECT * FROM count WHERE name='keywords'"
        # cursor.execute(query)
        # data = cursor.fetchone()
        # val = data[1] if data else 0
        # if id >= val:
        #     query = "UPDATE count SET value = value - 1 WHERE name='keywords'"
        #     cursor.execute(query)
    connection.commit()
    flash("Keyword deleted successfully", "manual")
    return redirect(url_for('Keyword'))

@app.route('/uploadcsv', methods=['GET', 'POST'])
def UploadKeyword():
    csvfile = request.files['csvfile']
    if csvfile:
        csv_data = csvfile.read().decode('utf-8').splitlines()
        csv_reader = csv.reader(csv_data)
        keywords = [item for sublist in csv_reader for item in sublist]
        with connection.cursor() as cursor:
            for keyword in keywords:
                cursor.execute("SELECT COUNT(*) FROM keywords WHERE keywords = %s", (keyword,))
                result = cursor.fetchone()
                keyword_exists = result[0] > 0
                if not keyword_exists:
                    query = "INSERT INTO keywords (keywords) VALUES (%s)"
                    cursor.execute(query, (keyword,))
        connection.commit()
        flash('CSV file uploaded successfully', 'upload')
        return redirect(url_for('Keyword'))
    flash('Error uploading CSV file', 'upload')
    return redirect(url_for('Keyword'))

# Dorker - done
@app.route('/dorker')
@login_required
def Dorker():
    with connection.cursor() as cursor:
        user = current_user.username
        query = "SELECT * FROM dorkedlinks"
        cursor.execute(query)
        dorkedlinks = cursor.fetchall()
        query = "SELECT * FROM count WHERE name='dorkedlinks'"
        cursor.execute(query)
        count_data = cursor.fetchone()
        val = count_data[1] if count_data else 0
    return render_template('dorker.html', user=user, dorkedlinks=dorkedlinks, val=val)

@app.route('/adddorkedlink', methods=['POST'])
@login_required
def AddDorkedLink():
    if request.method == 'POST':
        keyword=request.form.get('keyword')
        page=request.form.get('page')
        engine=request.form.get('engine')
        if engine == "google":
            links = Dork.Google(keyword, int(page))
        elif engine == "duckduckgo":
            links = Dork.Duckduckgo(keyword, int(page))
        elif engine == "bing":
            links = Dork.Bing(keyword, int(page))
        with connection.cursor() as cursor:
            for link in links:
                cursor.execute("SELECT COUNT(*) FROM dorkedlinks WHERE link = %s", (link,))
                result = cursor.fetchone()
                link_exists = result[0] > 0
                if not link_exists:
                    query = "INSERT INTO dorkedlinks (link) VALUES (%s)"
                    cursor.execute(query, (link,))
        check = "done"
        connection.commit()
        if check:
            flash("Dorking successful", "manual")
        else:
            flash("Dorking failed", "manual")
    return redirect(url_for('Dorker'))

@app.route('/dorkdb', methods=['POST'])
@login_required
def DorkDB():
    if request.method == 'POST':
        keywordn=request.form.get('keyword')
        page=request.form.get('page')
        engine=request.form.get('engine')
        with connection.cursor() as cursor:
            query = "SELECT * FROM count WHERE name='keywords'"
            cursor.execute(query)
            count_data = cursor.fetchone()
            val = count_data[1] if count_data else 0
            query = f"SELECT * FROM keywords WHERE id > {int(val)} LIMIT {int(keywordn)};"
            cursor.execute(query)
            fkeywords = cursor.fetchall()
            keywords = [item[1] for item in fkeywords]
            update_val = fkeywords[-1][0]
            links = []
            for keyword in keywords:
                if engine == "google":
                    link = Dork.Google(keyword, int(page))
                    for l in link:
                        links.append(l)
                elif engine == "duckduckgo":
                    link = Dork.Duckduckgo(keyword, int(page))
                    for l in link:
                        links.append(l)
                elif engine == "bing":
                    link = Dork.Bing(keyword, int(page))
                    for l in link:
                        links.append(l)
            for link in links:
                cursor.execute("SELECT COUNT(*) FROM dorkedlinks WHERE link = %s", (link,))
                result = cursor.fetchone()
                link_exists = result[0] > 0
                if not link_exists:
                    query = "INSERT INTO dorkedlinks (link) VALUES (%s)"
                    cursor.execute(query, (link,))
            check = "done"
            query = f"UPDATE count SET value = {update_val} WHERE name='keywords'"
            cursor.execute(query)
        connection.commit()
        if check:
            flash("Dorking successful", "db")
        else:
            flash("Dorking failed", "db")
    return redirect(url_for('Dorker'))

@app.route('/deletedorkedlink/<int:id>')
@login_required
def DeleteDorkedLink(id):
    with connection.cursor() as cursor:
        query = "DELETE FROM dorkedlinks WHERE id = %s"
        cursor.execute(query, (id,))
        # query = "SELECT * FROM count WHERE name='dorkedlinks'"
        # cursor.execute(query)
        # data = cursor.fetchone()
        # val = data[1] if data else 0
        # if id >= val:
        #     query = "UPDATE count SET value = value - 1 WHERE name='dorkedlinks'"
        #     cursor.execute(query)
    connection.commit()
    flash("Link deleted successfully", "manual")
    return redirect(url_for('Dorker'))

# Onion Links Extractor - done
@app.route('/onionlinksextractor')
@login_required
def OnionLinksExtractor():
    with connection.cursor() as cursor:
        user = current_user.username
        query = "SELECT * FROM onionlinks"
        cursor.execute(query)
        keywords = cursor.fetchall()
        query = "SELECT * FROM count WHERE name='onionlinks'"
        cursor.execute(query)
        data = cursor.fetchone()
        val = data[1] if data else 0
    return render_template('onionlinksextractor.html', user=user, keywords=keywords, val=val)

@app.route('/onionscrapeurl', methods=['POST'])
@login_required
def OnionScrapeURL():
    if request.method == 'POST':
        url=request.form.get('url')
        OnionLinks = OnionLinkScraper.Scrape(url)
        with connection.cursor() as cursor:
            for link in OnionLinks:
                cursor.execute("SELECT COUNT(*) FROM onionlinks WHERE link = %s", (link,))
                result = cursor.fetchone()
                link_exists = result[0] > 0
                if not link_exists:
                    query = "INSERT INTO onionlinks (link) VALUES (%s)"
                    cursor.execute(query, (link,))
        check = "done"
        connection.commit()
        if check:
            flash(f"Scraping successful. {len(OnionLinks)} Links found.", "manual")
        else:
            flash("Scraping failed", "manual")
    return redirect(url_for('OnionLinksExtractor'))

@app.route('/onionscrapedb', methods=['POST'])
@login_required
def OnionScrapeDB():
    if request.method == 'POST':
        num=request.form.get('num')
        with connection.cursor() as cursor:
            query = "SELECT * FROM count WHERE name='dorkedlinks'"
            cursor.execute(query)
            count_data = cursor.fetchone()
            val = count_data[1] if count_data else 0
            query = f"SELECT * FROM dorkedlinks WHERE id > {int(val)} LIMIT {int(num)};"
            cursor.execute(query)
            fdorkedlinks = cursor.fetchall()
            dorkedlinks = [item[1] for item in fdorkedlinks]
            update_val = fdorkedlinks[-1][0]
            links = []
            for dorkedlink in dorkedlinks:
                link = OnionLinkScraper.Scrape(dorkedlink)
                for l in link:
                    links.append(l)
            for link in links:
                cursor.execute("SELECT COUNT(*) FROM onionlinks WHERE link = %s", (link,))
                result = cursor.fetchone()
                link_exists = result[0] > 0
                if not link_exists:
                    query = "INSERT INTO onionlinks (link) VALUES (%s)"
                    cursor.execute(query, (link,))
            for onionlink in links:
                    cursor.execute("SELECT COUNT(*) FROM queue WHERE name = %s", (onionlink,))
                    result = cursor.fetchone()
                    onionlinkexists = result[0] > 0
                    if not onionlinkexists:
                        query = "INSERT INTO queue (name) VALUES (%s)"
                        cursor.execute(query, (onionlink,))
            connection.commit()
            check = "done"
            query = f"UPDATE count SET value = {update_val} WHERE name='dorkedlinks'"
            cursor.execute(query)
        connection.commit()
        if check:
            flash(f"Scraping successful. {len(links)} Links found.", "db")
        else:
            flash("Scraping failed", "db")
    return redirect(url_for('OnionLinksExtractor'))

@app.route('/deleteonionlink/<int:id>')
@login_required
def DeleteOnionLink(id):
    with connection.cursor() as cursor:
        query = "DELETE FROM onionlinks WHERE id = %s"
        cursor.execute(query, (id,))
        # query = "SELECT * FROM count WHERE name='onionlinks'"
        # cursor.execute(query)
        # data = cursor.fetchone()
        # val = data[1] if data else 0
        # if id >= val:
        #     query = "UPDATE count SET value = value - 1 WHERE name='onionlinks'"
        #     cursor.execute(query)
    connection.commit()
    flash("Onion Link deleted successfully", "manual")
    return redirect(url_for('OnionLinksExtractor'))

# Onion Links Importer
@app.route('/onionlinksimporter')
@login_required
def OnionLinksImporter():
    with connection.cursor() as cursor:
        user = current_user.username
        query = "SELECT * FROM onionlinks"
        cursor.execute(query)
        keywords = cursor.fetchall()
        query = "SELECT * FROM count WHERE name='onionlinks'"
        cursor.execute(query)
        data = cursor.fetchone()
        val = data[1] if data else 0
    return render_template('onionlinksimporter.html', user=user, keywords=keywords, val=val)

@app.route('/onionlinksupload', methods=['GET', 'POST'])
def OnionLinksUpload():
    csvfile = request.files['csvfile']
    if csvfile:
        csv_data = csvfile.read().decode('utf-8').splitlines()
        csv_reader = csv.reader(csv_data)
        onionlinks = [item for sublist in csv_reader for item in sublist]
        onionlinks = OnionLinkCleaner.Clean(onionlinks)
        with connection.cursor() as cursor:
            for onionlink in onionlinks:
                cursor.execute("SELECT COUNT(*) FROM onionlinks WHERE link = %s", (onionlink,))
                result = cursor.fetchone()
                onionlinkexists = result[0] > 0
                if not onionlinkexists:
                    query = "INSERT INTO onionlinks (link) VALUES (%s)"
                    cursor.execute(query, (onionlink,))
        connection.commit()
        with connection.cursor() as cursor:
            for onionlink in onionlinks:
                cursor.execute("SELECT COUNT(*) FROM queue WHERE name = %s", (onionlink,))
                result = cursor.fetchone()
                onionlinkexists = result[0] > 0
                if not onionlinkexists:
                    query = "INSERT INTO queue (name) VALUES (%s)"
                    cursor.execute(query, (onionlink,))
        connection.commit()
        flash('CSV file uploaded successfully', 'upload')
        return redirect(url_for('OnionLinksImporter'))
    flash('Error uploading CSV file', 'upload')
    return redirect(url_for('OnionLinksImporter'))

# Tor Relay
@app.route('/torrelay')
@login_required
def TorRelay():
    with connection.cursor() as cursor:
        cursor.execute("""SELECT id, name, ip_address, city, country, isp, consensus_weight, guard_probability, middle_probability, exit_probability FROM torrelayipdata""")
        data = cursor.fetchall()
    return render_template('torrelay/index.html', data=data)

@app.route('/torrelay/<id>')
@login_required
def TorRelayData(id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM torrelayipdata WHERE id = %s", (id,))
        row = cursor.fetchone()
    return render_template('torrelay/data.html', row=row)

# def IntelligenceGeneratorQueue():
#     while True:
#         try:
#             with connection.cursor() as cursor:
#                 cursor.execute("SELECT * FROM queue LIMIT 1;")
#                 result = cursor.fetchone()
#                 print("running")
#                 print(result)
#                 if result:
#                     Intelligence.intelligence(result[1])
#                     cursor.execute("DELETE FROM queue WHERE id = %s;", (result[0],))
#                     connection.commit()
#                     print("done")
#             time.sleep(3)
#         except Exception as e:
#             print(f"Error: {e}")

# def start_queue():
#     thread = Thread(target=IntelligenceGeneratorQueue)
#     thread.start()

# @app.route('/startqueue')
# @login_required
# def startqueue():
#     start_queue()
#     return "Queue started successfully."

@app.route('/reportgenerate/<path:url>')
@login_required
def startqueue(url):

    class TorSession:
        def __init__(self):
            self.tor_process = subprocess.Popen(["C:\\Tor Browser\\Browser\\TorBrowser\\Tor\\tor.exe"])
            self.proxies = {'http': 'socks5h://127.0.0.1:9050', 'https': 'socks5h://127.0.0.1:9050'}
            self.session = requests.Session()
            self._configure_retry_policy()

        def _configure_retry_policy(self):
            retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
            adapter = HTTPAdapter(max_retries=retries)
            self.session.mount('http://', adapter)
            self.session.mount('https://', adapter)

        def get(self, url):
            try:
                response = self.session.get(url, proxies=self.proxies)
                response.raise_for_status()
                return response
            except RequestException as e:
                print(f"Error accessing the URL: {e}")
                return None

        def terminate(self):
            self.tor_process.terminate()

    TorSession = TorSession()

    report = NewReport.Main(url, TorSession)

    TorSession.terminate()

    # json_report = json.dumps(report)
    # mongo.db.Intelligence.insert_one(json.loads(json_report))

    return report

if __name__ == '__main__':
    
    app.run(debug=True, host='0.0.0.0', port=3333)