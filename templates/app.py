import os
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import psycopg2
from dotenv import load_dotenv
import boto3

load_dotenv()

app = Flask(__name__)

s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# koneksi database
conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    database=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    port=os.getenv('DB_PORT')
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    nama = request.form['nama']
    email = request.form['email']
    foto = request.files['foto']

    if foto:
        filename = secure_filename(foto.filename)

        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        # foto.save(filepath)

        # foto_url = f'/uploads/{filename}'

        s3.upload_fileobj(
            foto,
            os.getenv('AWS_BUCKET_NAME'),
            filename,
            ExtraArgs={
                "ContentType": foto.content_type
            }
        )

        foto_url = f"https://{os.getenv('AWS_BUCKET_NAME')}.s3.amazonaws.com/{filename}"

        cur = conn.cursor()

        query = """
        INSERT INTO pelamar (nama, email, foto_url)
        VALUES (%s, %s, %s)
        """

        cur.execute(query, (nama, email, foto_url))
        conn.commit()

        cur.close()

        return f'''
        <h2>Data berhasil disimpan!</h2>
        <p>Nama: {nama}</p>
        <p>Email: {email}</p>
        <img src="{foto_url}" width="200">
        <br><br>
        <a href="/">Kembali</a>
        '''

    return 'Upload gagal'

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    from flask import send_from_directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)