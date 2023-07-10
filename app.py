# Import Library
import sqlite3
import os
from flask import Flask, flash, request, redirect, url_for, render_template, Markup, jsonify
from werkzeug.utils import secure_filename
from flask import send_from_directory
import pandas as pd
import re

# Hapus Stopwords
import nltk
nltk.download('punkt')
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
nltk.download('stopwords')
nltk.corpus.stopwords.words('indonesian')

# Swagger
from flasgger import Swagger, LazyString, LazyJSONEncoder
from flasgger import swag_from

app = Flask(__name__, template_folder='templates')
app.secret_key = 'abednigo'


####Kemungkinan tidak dibutuhkan, jadi bisa dioverride/direvisi
def cleansing(text):
    
    # Mengubah kalimat menjadi huruf kecil
    text = text.lower()

    # Menghapus hastag
    pola_1 = r'#([^\s]+)'
    text = re.sub(pola_1, '', text)

    # Menghapus mention
    pola_2 = r'@[^\s]+'
    text = re.sub(pola_2, '', text)

    # Menghapus user, retweet, \t, \r, url, xd, orang, kalo
    pola_3 = r'(user|retweet|\\t|\\r|url|xd|orang|kalo)'
    text = re.sub(pola_3, '', text)

    # Menghapus single character
    pola_4 = r'\b\w{1,3}\b'
    text = re.sub(pola_4, '', text)

    # Menghapus tanda baca, karakter operasi matematika, dll.
    pola_5 = r'[\,\@\*\_\-\!\:\;\?\'\.\"\)\(\{\}\<\>\+\%\$\^\#\/\`\~\|\&\|]'
    text = re.sub(pola_5, ' ', text)
    
    # Menghapus emoji
    pola_6 = r'\\[a-z0-9]{1,5}'
    text = re.sub(pola_6, '', text)

    # Menghapus karekter yang bukan termasuk ASCII
    pola_7 = r'[^\x00-\x7f]'
    text = re.sub(pola_7, '', text)

    # Menghapus url yang diawali dengan http atau https
    pola_8 = r'(https|https:)'
    text = re.sub(pola_8, '', text)

    # Menghapus karakter '\',  '[',  ']'
    pola_9 = r'[\\\]\[]'
    text = re.sub(pola_9, '', text)

    # Menghapus "wkwkwk"
    pola_10 = r'\bwk\w+'
    text = re.sub(pola_10, '', text)

    # Menghapus digit karakter
    pola_11 = r'\d+'
    text = re.sub(pola_11, '', text)

    # Menghapus karekter yang bukan termasuk ASCII
    pola_12 = r'(\\u[0-9A-Fa-f]+)'
    text = re.sub(pola_12, '', text)
    
    # Menghapus spasi yang berlebih
    pola_13 = r'(\s+|\\n)'
    text = re.sub(pola_13, ' ', text)
    
    # Menghapus spasi pada kalimat pertama dan terakhir
    text = text.rstrip()
    text = text.lstrip()
    return text

def replaceThreeOrMore(text):
    # Menghapus tiga atau lebih pengulangan karakter termasuk newlines.
    pattern = re.compile(r"(.)\1{1,}", re.DOTALL)
    return pattern.sub(r"\1\1", text)

indo_stop_words = stopwords.words("indonesian")

def remove_stopwords(text):
    return ' '.join([word for word in word_tokenize(text) if word not in indo_stop_words])
### Catatan: Indo stop words ini bisa diganti dengan list_abusive_words, diganti ke list formal words, dan bisa diskip

##### Tampilan Dasbor Halaman Utama as .html
@app.route("/", methods=['GET'])
def home():
    return render_template('home.html')

##### Membaca File, Menampilkan Dataframe .HTML #####
@app.route("/data_before_cleansing", methods=["GET", "POST"])
def read_file_to_html():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        csv_file = request.files.get("file") ### Catatan: Ambil CSV nya, kalau bukan, jadi invalid file
        if not csv_file or not csv_file.filename.endswith('.csv'):
            return 'Invalid file'

    # Membaca file .csv
        df = pd.read_csv(csv_file, encoding='latin-1')

        conn = sqlite3.connect('database.db') ### Catatan: kemungkinan Redundant
        cursor = conn.cursor() ### Catatan: kemungkinan Redundant
        table = df.to_sql('challenge', conn, if_exists='replace') ### Catatan: dilihat dulu hasilnya # to prove that this code is running well, drop the "upload_and_download_csv_file" table first from the database via the app_sqlite.py file
        conn.commit()
        conn.close()

        df = df.to_html(index=False, justify='left') ###Catatan : render jadi html

        return Markup(df)

    # Jika memakai Method .get
    return render_template("file.html")


##### UPLOAD FILE #####

@app.route("/data_after_cleansing", methods=["GET", "POST"])
def upload_file():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    if request.method == "POST":
        csv_file = request.files.get("file")
        if not csv_file or not csv_file.filename.endswith('.csv'):
            return 'Invalid file'

    # Membaca file .csv 
        df = pd.read_csv(csv_file, encoding='latin-1')

    # Menerapkan Function Data Cleansing kedalam Dataframe
        df = df.select_dtypes(include=['object']).applymap(cleansing)

    # Menerapkan Function untuk menghapus tiga atau lebih pengulangan karakter termasuk newlines.
        df_clean = df.applymap(replaceThreeOrMore)

    # Mendefine stopwords dalam bahasa Indonesia
        indo_stop_words = stopwords.words("indonesian")

    # Menerapkan function ke semua kolom yang pada dataframe
        table = df_clean.applymap(remove_stopwords)

    # Mengubah dataframe kedalam bentuk tabel HTML
        # Mengganti tabel yang ada dengan data yang sudah dibersihkan.
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        table = table.to_sql('challenge_cleaned', conn, if_exists='replace') # to prove that this code is running well, drop the "challenge" table from the database via the app_sqlite.py file
        conn.close()

    # Return tabel HTML sebagai respon dari form submission
        table_2 = df_clean.select_dtypes(include=['object']).applymap(remove_stopwords)
        table_2 = table_2.to_html()
        return Markup(table_2)

  # Jika memakai Method .get gunakan form dari template
    return render_template("file.html")


##### Upload File CSV, Bersihkan, dan Download #####
app.config['UPLOAD_FOLDER'] = ''
app.config['ALLOWED_EXTENSIONS'] = {'csv'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/upload_download_file', methods=['GET', 'POST'])
def upload_download_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        directory_path = request.form.get("directory_path")
        filename = request.form.get("filename")

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            if not filename:
                filename = secure_filename(file.filename)
        else:
            filename = secure_filename(filename)
        if file and allowed_file(file.filename):
            if directory_path:
                app.config['UPLOAD_FOLDER'] = directory_path
            else:
                app.config['UPLOAD_FOLDER'] = "C:/Users/nigon/Binar Academy/Challenge-Gold"
            if not filename:
                filename = secure_filename(file.filename)
            else:
                filename = secure_filename(filename)

            df = pd.read_csv(file, encoding='latin-1')
            df = df.select_dtypes(include=['object']).applymap(cleansing)
            df = df.applymap(replaceThreeOrMore)
            df_clean = df.select_dtypes(include=['object']).applymap(remove_stopwords)
            # Specify the target directory path
            target_directory = r"C:/Users/nigon/Binar Academy/Challenge-Gold"
            os.makedirs(target_directory, exist_ok=True)
            df_clean.to_csv(os.path.join(target_directory, "data_clean.csv"), index=False, encoding='latin-1')

            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            table = df.to_sql('upload_and_download_csv_file', conn, if_exists='replace')
            conn.close()

            flash('The file has been uploaded and cleaned data is saved to the directory {} as data_clean.csv'.format(app.config['UPLOAD_FOLDER']))
            return redirect(url_for('upload_download_file', name=df_clean))
    return render_template('download_file.html')


##### Data Cleansing Berdasarkan Index ##### 
@app.route("/cleansing_tweet_column", methods=['GET', 'POST'])
def index():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    if request.method == 'POST':
        # Mengambil value dari row data
        before = request.form.get('before')

        # Mengubah isi dari baris kedalam integer
        before = int(before)

        # Pilih baris yang digunakan sebelumnya dan terapkan function data cleansing
        cursor.execute('''SELECT * FROM challenge''')
        df = pd.read_sql_query('''SELECT * FROM challenge''', conn)
        conn.commit()
        values_data = df[['Tweet']].iloc[before].apply(cleansing)

        # Menerapkan function replaceThreeOrMore
        values_data = values_data.apply(replaceThreeOrMore)

        # men-define stopwords dalam Indonesian
        indo_stop_words = stopwords.words("indonesian")

        # Function untuk menghapus stopwords
        def remove_stopwords(text):
            return ' '.join([word for word in word_tokenize(text) if word not in indo_stop_words])

        # Menerapkan function remove_stopwords pada dataframe
        table = values_data.apply(remove_stopwords)

        # Ubah format value kedalam bentuk list
        values_str = table.to_list()

        # Pilih baris yang akan digunakan
        cursor.execute('''SELECT * FROM challenge''')
        df = pd.read_sql_query('''SELECT * FROM challenge''', conn)
        conn.commit()
        before_data = df[['Tweet']].iloc[before]

        # Ubah format value kedalam bentuk list
        before_pre = before_data.to_list()
        conn.close()

        return redirect(url_for("by_index", clean=values_str, before=before_pre))

    return render_template("index_2.html")


@app.route("/by_index", methods=['GET'])
def by_index():
    clean = request.args.get('clean')
    before = request.args.get('before')
    return f'''
    TWEET BEFORE PREPROCESSING (CLEANSING): <br> <br> {before} <br> <br> <br> <br> <br>
    TWEET AFTER PREPROCESSING (CLEANSING): <br> <br> {clean}
    '''

##### PREPROCESSING TEXT (INPUT TEXT) #####
@app.route("/text_cleansing", methods=['GET', 'POST'])
def clean():
    if request.method == 'POST':
        tweet = request.form['tweet']
        clean_text = cleansing(tweet)
        result = replaceThreeOrMore(clean_text)
            
        return redirect(url_for("cleansing", text=result))

    return render_template("input_text.html")

@app.route("/<text>", methods=['GET'])
def cleansing(text):
    return f'Cleansing result: {text}'



##### -------------------------------------SWAGGER---------------------------------------- #####


app.json_encoder = LazyJSONEncoder
swagger_template = dict(
info = {
    'title': LazyString(lambda: 'API Documentation for Data Processing and Modeling'),
    'version': LazyString(lambda: '1.0.0'),
    'description': LazyString(lambda: 'Dokumentasi API untuk Data Processing dan Modeling'),
    },
    host = LazyString(lambda: request.host)
)
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'docs',
            "route": '/docs.json'
        }
    ],
    "static_url_path": "/flagger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}

swagger = Swagger(app, template=swagger_template, config=swagger_config)

def cleansing(text):
    # Mengubah kalimat menjadi huruf kecil
    text = text.lower()

    # Menghapus hastag
    pola_1 = r'#([^\s]+)'
    text = re.sub(pola_1, '', text)

    # Menghapus mention
    pola_2 = r'@[^\s]+'
    text = re.sub(pola_2, '', text)

    # Menghapus user, retweet, \t, \r, url, xd, orang, kalo
    pola_3 = r'(user|retweet|\\t|\\r|url|xd|orang|kalo)'
    text = re.sub(pola_3, '', text)

    # Menghapus single character
    pola_4 = r'\b\w{1,3}\b'
    text = re.sub(pola_4, '', text)

    # Menghapus tanda baca, karakter operasi matematika, dll.
    pola_5 = r'[\,\@\*\_\-\!\:\;\?\'\.\"\)\(\{\}\<\>\+\%\$\^\#\/\`\~\|\&\|]'
    text = re.sub(pola_5, ' ', text)
    
    # Menghapus emoji
    pola_6 = r'\\[a-z0-9]{1,5}'
    text = re.sub(pola_6, '', text)

    # Menghapus karekter yang bukan termasuk ASCII
    pola_7 = r'[^\x00-\x7f]'
    text = re.sub(pola_7, '', text)

    # Menghapus url yang diawali dengan http atau https
    pola_8 = r'(https|https:)'
    text = re.sub(pola_8, '', text)

    # Menghapus karakter '\',  '[',  ']'
    pola_9 = r'[\\\]\[]'
    text = re.sub(pola_9, '', text)

    # Menghapus "wkwkwk"
    pola_10 = r'\bwk\w+'
    text = re.sub(pola_10, '', text)

    # Menghapus digit karakter
    pola_11 = r'\d+'
    text = re.sub(pola_11, '', text)

    # Menghapus karekter yang bukan termasuk ASCII
    pola_12 = r'(\\u[0-9A-Fa-f]+)'
    text = re.sub(pola_12, '', text)
    
    # Menghapus spasi yang berlebih
    pola_13 = r'(\s+|\\n)'
    text = re.sub(pola_13, ' ', text)
    
    # Menghapus spasi pada kalimat pertama dan terakhir
    text = text.rstrip()
    text = text.lstrip()
    return text

def replaceThreeOrMore(text):
    # Menghapus tiga atau lebih pengulangan karakter termasuk newlines.
    pattern = re.compile(r"(.)\1{1,}", re.DOTALL)
    return pattern.sub(r"\1\1", text)

indo_stop_words = stopwords.words("indonesian")

def remove_stopwords(text):
    return ' '.join([word for word in word_tokenize(text) if word not in indo_stop_words]) 


##################################################################################################################


##### UPLOADING FILE TO CLEAN THE DATA, THEN SEE THE RESULTS AS JSON ON SWAGGER, AND STORE THE FILE TO DATABASE #####
@swag_from("./templates/swag_clean.yaml", methods=['POST'])
@app.route('/upload_file_to_clean_see_as_json_and_store_to_database', methods=['POST'])
def upload_file_swgr_json():
    conn = sqlite3.connect('database/challenge_level_3.db')
    cursor = conn.cursor()
    if request.method == "POST":
        csv_file = request.files.get("file")
        if not csv_file or not csv_file.filename.endswith('.csv'):
            return 'Invalid file'

    # Baca file .csv
        df = pd.read_csv(csv_file, encoding='latin-1')

    # Menerapkan function data cleansing
        df = df.select_dtypes(include=['object']).applymap(cleansing)

    # Menerapkan Function untuk menghapus tiga atau lebih pengulangan karakter termasuk newlines
        df_clean = df.applymap(replaceThreeOrMore)

    # Menerapkan function ke semua kolom yang pada dataframe
        table = df_clean.applymap(remove_stopwords)

    # Mengubah dataframe kedalam bentuk tabel HTML
        # Mengubah tabel yang ada dengan data yang sudah dibersihkan
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        table = table.to_sql('challenge_cleaned_flask_swagger', conn, if_exists='replace') # to prove that this code is running well, drop the "challenge_cleaned_flask_swagger" table from the database via the app_sqlite.py file
        conn.close()

    # Mengembalikan tabel HTML sebagai Respon dari form submission
        table_2 = df_clean.select_dtypes(include=['object']).applymap(remove_stopwords)

    # Mengubah dataframe kedalam bentuk tabel HTML
        table = table_2.to_json()

    return table


###################################################################################################


##### Upload File, Bersihkan, Kemudian Download, dan Kirim kedalam Database #####
app.config['UPLOAD_FOLDER'] = ''
app.config['ALLOWED_EXTENSIONS'] = {'csv'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@swag_from("./templates/swag_clean.yaml", methods=['POST'])
@app.route('/upload_file_to_clean_download_and_store_to_database', methods=['POST'])
def upload_file_swgr_download():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    if request.method == "POST":
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        directory_path = request.form.get("directory_path")
        print(directory_path)
        filename = request.form.get("filename")
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            if not filename:
                filename = secure_filename(file.filename)
        else:
            filename = secure_filename(filename)
        if file and allowed_file(file.filename):
            if directory_path:
                app.config['UPLOAD_FOLDER'] = directory_path
            else:
                if 'UPLOAD_FOLDER' not in app.config:
                    app.config['UPLOAD_FOLDER'] = "C:/Users/nigon/Binar Academy/Challenge Gold"

            if not filename:
                filename = secure_filename(file.filename)
            else:
                filename = secure_filename(filename)

            df = pd.read_csv(file, encoding='latin-1')
            df = df.select_dtypes(include=['object']).applymap(cleansing)
            df = df.applymap(replaceThreeOrMore)
            df_clean = df.select_dtypes(include=['object']).applymap(remove_stopwords)
            df_clean.to_csv(os.path.join(app.config['UPLOAD_FOLDER'], "data_clean.csv"), index=False, encoding='latin-1')

    # Mengubah dataframe kedalam bentuk tabel HTML
        # Mengubah tabel yang ada dengan data yang sudah dibersihkan
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            table = df_clean.to_sql('challenge_cleaned_flask_swagger_download_file', conn, if_exists='replace') # to prove that this code is running well, drop the "challenge_cleaned_flask_swagger" table from the database via the app_sqlite.py file
            conn.close()

        flash('The file has been uploaded and downloaded to the directory {} as data_clean.csv'.format(app.config['UPLOAD_FOLDER']))
        table = df_clean.to_json()
        return redirect(url_for('upload_download_file', name=df_clean))
    return table


@swag_from("./templates/text_clean.yaml", methods=['POST'])
@app.route('/cleansing_text', methods=['POST'])
def text_cleansing_swgr():
    if request.method == 'POST':
        text = request.form.get('text')

    # Menerapkan function data Cleansing kesetiap baris yang ada pada dataframe
        process_text = cleansing(text)

    # Menerapkan Function untuk menghapus tiga atau lebih pengulangan karakter termasuk newlines
        cleaned_text = replaceThreeOrMore(process_text)
    
    return cleaned_text


################################################################################################


# Bersihkan dataframe berdasarkan index, kemduian tampolkan hasil dalam bentuk JSON
@swag_from("./templates/swagger_index.yaml", methods=['POST'])
@app.route("/Clean dataframe by index. Choose 0 - 13168", methods=['GET','POST'])
def index_swgr():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    if request.method == 'POST':
        # Mengambil value dari row data
        index = int(request.form.get('index'))

        # Pilih row yang ingin digunakan sebelumny, kemudia terapkan function data cleansing
        cursor.execute('''SELECT * FROM challenge''')
        df = pd.read_sql_query('''SELECT * FROM challenge''', conn)
        conn.commit()
        values_data = df[['Tweet']].iloc[index].apply(cleansing)

        # Menerapkan function replaceThreeOrMore
        values_data = values_data.apply(replaceThreeOrMore)

        # Menerapkan function remove_stopwords
        table = values_data.apply(remove_stopwords)

        # Ubah format value kedalam bentuk list
        values_str = table.to_list()

        # Pilih baris yang ingin digunakan
        cursor.execute('''SELECT * FROM challenge''')
        df = pd.read_sql_query('''SELECT * FROM challenge''', conn)
        conn.commit()
        before_data = df[['Tweet']].iloc[index]

        # Ubah format value kedalam bentuk list
        before_pre = before_data.to_list()
        conn.close()

    return jsonify(clean=values_str, before=before_pre)

##### Upload file, bersihkan, dan tampilkan sebagai JSON #####
@swag_from("./templates/swag_clean.yaml", methods=['POST'])
@app.route("/data_before_cleansing_swagger", methods=["GET", "POST"])
def read_file_to_json():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    if request.method == 'POST':
        csv_file = request.files.get("file")
        if not csv_file or not csv_file.filename.endswith('.csv'):
            return 'Invalid file'

        df = pd.read_csv(csv_file, encoding='latin-1')

        # Ganti tabel yang ada dengan data yang suda dibersihkan
        table = df.to_sql('challenge', conn, if_exists='replace') 
        conn.commit()

    # Ubah dataframe kedalam bentuk JSON
        table = df.to_json()
        conn.close()
        return table

if __name__ == '__main__':
    app.run(debug=True)

