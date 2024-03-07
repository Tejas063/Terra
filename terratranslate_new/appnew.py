from flask import Flask, render_template, request, redirect, url_for, flash, session
from keras.models import load_model
from keras.preprocessing.image import img_to_array, load_img
from numpy import expand_dims
import os
from io import BytesIO
import base64
import numpy as np
import cv2
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from datetime import datetime

app = Flask(__name__)

app.secret_key = 'very-secret'
#model_50_epochs

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '@Tha_sql23'
app.config['MYSQL_DB'] = 'terratranslate'

mysql = MySQL(app)

# Load the Keras model
model = load_model('model_180.h5')

# Function to decode base64 and return binary data
def base64_to_binary(base64_string):
    return base64.b64decode(base64_string)

def load_image(image_bytes, size=(256,256)):
    image = load_img(BytesIO(image_bytes), target_size=size)
    pixels = img_to_array(image)
    pixels = (pixels - 127.5) / 127.5
    pixels = expand_dims(pixels, 0)
    return pixels

def array_to_img_base64(arr):
    arr = ((arr + 1) / 2.0 * 255).clip(0, 255).astype(np.uint8)[0]
    _, img_encoded = cv2.imencode('.png', cv2.cvtColor(arr, cv2.COLOR_RGB2BGR))
    img_base64 = base64.b64encode(img_encoded).decode('utf-8')
    return img_base64

@app.route('/')
def index():
    session_active  = session.get('loggedin')
    return render_template('index_beautiful.html',session_active=session_active)

@app.route('/login', methods =['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'userpassword' in request.form:
        username = request.form['username']
        userpassword = request.form['userpassword']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = % s AND userpassword = % s', (username, userpassword))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['userid'] = account['userid']
            session['username'] = account['username']
            return redirect(url_for('index'))
        else:
            msg = 'Incorrect username / password !'
    return render_template('login.html', msg = msg)
 
@app.route('/logout')
def logout():    
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('username', None)
    return redirect(url_for('login'))

 
@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST':
        username = request.form.get('username')
        userpassword = request.form.get('userpassword')
        email = request.form.get('email')

        if not username or not userpassword or not email:
            msg = 'Please fill out the form !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers !'
        else:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
            account = cursor.fetchone()
            if account:
                msg = 'Account already exists !'
            else:
                cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s)', (username, userpassword, email))
                mysql.connection.commit()
                msg = 'You have successfully registered !'
                return render_template('login.html', msg=msg)
    return render_template('register.html', msg=msg)

@app.route('/history')
def getImages():
    msg = ''
    userid = session.get('userid')
    cur = mysql.connection.cursor()
    
    cur.execute("SELECT src_image, gen_image, imagedatetime, src_images_size, gen_images_size FROM userimages WHERE userid = %s",(userid ,))
    fetched_data = cur.fetchall()
    cur.close()
    data = []
    for src_image, gen_image, imagedatetime, src_images_size, gen_images_size in fetched_data:
        src_base64 = base64.b64encode(src_image).decode('utf-8')
        gen_base64 = base64.b64encode(gen_image).decode('utf-8')
        imagedatetime = imagedatetime
        src_images_size = src_images_size
        gen_images_size= gen_images_size
        data.append((src_base64, gen_base64,imagedatetime,src_images_size,gen_images_size))
    return render_template('history.html',data=data)

@app.route("/process_image", methods=["POST"])
def upload_file():
    msg = ''
    checksession = session.get('loggedin')
    if checksession:
        userid = session.get('userid')
        gen_image = None
        src_image = None
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            file = request.files['file']
            file_bytes = file.read()
            src_image = load_image(file_bytes)
            gen_image = model.predict(src_image)
            gen_image = array_to_img_base64(gen_image)
            src_image = array_to_img_base64(src_image)
            gen_image_size = len(base64_to_binary(gen_image)) / 1024
            src_image_size = len(base64_to_binary(src_image)) / 1024
            current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO userimages (userid,src_image, gen_image, imagedatetime, src_images_size,gen_images_size) VALUES (%s, %s, %s, %s, %s, %s)",
                        (userid,base64_to_binary(src_image),
                         base64_to_binary(gen_image),
                         current_datetime,
                         src_image_size,
                         gen_image_size))
            mysql.connection.commit()
            cur.close()
    else:
        msg = "user not logged in"
        return render_template("index_beautiful.html",msg=msg)
    return render_template("index_beautiful.html", gen_image=gen_image, src_image=src_image)

if __name__ == "__main__":
    app.run(debug=True)
