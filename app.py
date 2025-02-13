from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for sessions
DATABASE = 'database.db'
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# تحديث قاعدة البيانات
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute(''' 
            CREATE TABLE IF NOT EXISTS missing_persons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER,
                gender TEXT,
                national_id TEXT UNIQUE,
                description TEXT,
                family_contact TEXT,
                reporter_name TEXT,
                reporter_contact TEXT,
                image_path TEXT,
                gps_latitude REAL,
                gps_longitude REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

def insert_missing_person(data):
    with sqlite3.connect(DATABASE) as conn:
        conn.execute(''' 
            INSERT INTO missing_persons (name, age, gender, national_id, description, family_contact, 
                reporter_name, reporter_contact, image_path, gps_latitude, gps_longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)

@app.route('/')
def index():
    # Check if user is logged in
    if 'username' in session:
        return render_template('index.html')
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check credentials
        if username == 'admin' and password == 'admin':
            session['username'] = username  # Store the username in session
            return redirect(url_for('index'))  # Redirect to homepage after successful login
        else:
            return render_template('login.html', error="اسم المستخدم أو كلمة المرور غير صحيحة.")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove the username from the session
    return redirect(url_for('login'))  # Redirect to login page

@app.route('/add', methods=['GET', 'POST'])
def add_person():
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in
    
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        national_id = request.form['national_id']
        description = request.form['description']
        family_contact = request.form['family_contact']
        reporter_name = request.form['reporter_name']
        reporter_contact = request.form['reporter_contact']
        gps_latitude = request.form['gps_latitude']
        gps_longitude = request.form['gps_longitude']

        # Save image
        image_path = None
        if 'image' in request.files:
            image = request.files['image']
            if image.filename:
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_path = f'static/uploads/{filename}'

        # Insert data into the database
        insert_missing_person((name, age, gender, national_id, description, family_contact, 
                               reporter_name, reporter_contact, image_path, gps_latitude, gps_longitude))
        return redirect(url_for('view_persons'))

    return render_template('report.html')

@app.route('/view')
def view_persons():
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in

    with sqlite3.connect(DATABASE) as conn:
        persons = conn.execute('SELECT * FROM missing_persons').fetchall()
    return render_template('view.html', persons=persons)

@app.route('/person/<int:person_id>')
def person_detail(person_id):
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in

    with sqlite3.connect(DATABASE) as conn:
        person = conn.execute('SELECT * FROM missing_persons WHERE id = ?', (person_id,)).fetchone()
    return render_template('person_detail.html', person=person)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
