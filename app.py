from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from deepface import DeepFace

app = Flask(__name__)

EMAIL_ADDRESS = 'titanwebhelp@gmail.com'
EMAIL_PASSWORD = "ipkwkwrrmnhjmkja"
SECURITY_EMAIL = "helpteamusa@gmail.com"

REPORT2_FOLDER = 'static/report2'
os.makedirs(REPORT2_FOLDER, exist_ok=True)
os.makedirs('static/uploads', exist_ok=True)

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        birthdate TEXT NOT NULL,
        gender TEXT NOT NULL,
        missing_date TEXT NOT NULL,
        wilaya TEXT NOT NULL,
        blood_group TEXT NOT NULL,
        other_details TEXT,
        reporter_full_name TEXT NOT NULL,
        phone_number TEXT NOT NULL,
        id_number TEXT NOT NULL,
        image_path TEXT,
        status TEXT DEFAULT 'Pending',
        created_at TEXT NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS statements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reporter_full_name TEXT NOT NULL,
        phone_number TEXT NOT NULL,
        id_number TEXT NOT NULL,
        image_path TEXT,
        other_details TEXT,
        related_report_id INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(related_report_id) REFERENCES reports(id)
    )''')
    conn.commit()
    conn.close()

def send_email_notification(subject, body):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = SECURITY_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, SECURITY_EMAIL, msg.as_string())
        server.quit()
    except Exception as e:
        None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/report', methods=['GET', 'POST'])
def report():
    if request.method == 'POST':
        full_name = request.form['fullName']
        birthdate = request.form['birthdate']
        gender = request.form['gender']
        missing_date = request.form['missingDate']
        wilaya = request.form['wilaya']
        blood_group = request.form['bloodGroup']
        other_details = request.form['otherDetails']
        reporter_full_name = request.form['reporterFullName']
        phone_number = request.form['phoneNumber']
        id_number = request.form['idNumber']
        image = request.files.get('image')

        image_path = None
        if image and image.filename != '':
            image_path = os.path.join('static/uploads', image.filename)
            image.save(image_path)
            print(f"Image saved at: {image_path}")

        created_at = datetime.now().isoformat()
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('''INSERT INTO reports (
            full_name, birthdate, gender, missing_date, wilaya, blood_group, 
            other_details, reporter_full_name, phone_number, id_number, image_path, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
            full_name, birthdate, gender, missing_date, wilaya, blood_group,
            other_details, reporter_full_name, phone_number, id_number, image_path, created_at
        ))
        report_id = c.lastrowid
        conn.commit()
        conn.close()

        report_data = {
            'full_name': full_name, 'birthdate': birthdate, 'gender': gender,
            'missing_date': missing_date, 'wilaya': wilaya, 'blood_group': blood_group,
            'other_details': other_details, 'reporter_full_name': reporter_full_name,
            'phone_number': phone_number, 'id_number': id_number, 'image_path': image_path,
            'created_at': created_at
        }
        send_email_notification("New Missing Person Report", 
            f"New report submitted:\n\n{str(report_data)}")

        return redirect(url_for('index'))  # Redirect to dashboard after adding report
    return render_template('report.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        gender = request.form.get('gender', '')
        state = request.form.get('state', '')
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        query = "SELECT * FROM reports WHERE status = 'Accepted'"
        params = []
        if gender:
            query += " AND gender = ?"
            params.append(gender)
        if state:
            query += " AND wilaya = ?"
            params.append(state)
        c.execute(query, params)
        results = c.fetchall()
        conn.close()

        return render_template('search.html', results=results)
    return render_template('search.html', results=None)

@app.route('/statement/<int:report_id>', methods=['GET', 'POST'])
def statement(report_id):
    if request.method == 'POST':
        reporter_full_name = request.form['reporterFullName']
        phone_number = request.form['phoneNumber']
        id_number = request.form['idNumber']
        other_details = request.form['otherDetails']
        image = request.files.get('image')

        image_path = None
        if image and image.filename != '':
            image_path = os.path.join(REPORT2_FOLDER, image.filename)
            image.save(image_path)
            None

        created_at = datetime.now().isoformat()
        is_match = False

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT image_path, full_name FROM reports WHERE id = ?", (report_id,))
        report = c.fetchone()
        if report and image_path and report[0]:
            try:
                result = DeepFace.verify(image_path, report[0], model_name="Facenet")
                is_match = result['verified']
                print(f"Face match result for report {report_id}: {result}")
            except Exception as e:
                None

        c.execute('''INSERT INTO statements (
            reporter_full_name, phone_number, id_number, image_path, other_details, related_report_id, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)''', (
            reporter_full_name, phone_number, id_number, image_path, other_details, report_id, created_at
        ))
        statement_id = c.lastrowid
        conn.commit()
        conn.close()

        if is_match:
            statement_data = {
                'reporter_full_name': reporter_full_name, 'phone_number': phone_number,
                'id_number': id_number, 'other_details': other_details, 'image_path': image_path,
                'related_report_id': report_id, 'created_at': created_at, 'missing_person_name': report[1]
            }
            send_email_notification("Match Found in Statement",
                f"A statement matches missing person '{report[1]}' (Report ID: {report_id}):\n\n{str(statement_data)}")

        return redirect(url_for('index'))  # Redirect to dashboard after adding statement
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT full_name FROM reports WHERE id = ?", (report_id,))
    report = c.fetchone()
    conn.close()
    if report:
        return render_template('statement.html', report_id=report_id, missing_person_name=report[0])
    return "Report not found", 404

@app.route('/dashboard')
def dashboard():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''SELECT r.id, r.full_name, r.birthdate, r.missing_date, r.wilaya, r.blood_group, r.status,
                        s.id AS statement_id, s.created_at AS statement_created_at
                 FROM reports r
                 LEFT JOIN statements s ON r.id = s.related_report_id
                 WHERE s.id = (SELECT MAX(id) FROM statements WHERE related_report_id = r.id) OR s.id IS NULL''')
    reports_raw = c.fetchall()
    conn.close()

    # Format reports as dictionaries for easier template access
    reports = []
    for report in reports_raw:
        report_id, full_name, birthdate, missing_date, wilaya, blood_group, status, statement_id, statement_created_at = report
        age = datetime.now().year - int(birthdate[:4])
        reports.append({
            'id': report_id,
            'full_name': full_name,
            'age': age,
            'missing_date': missing_date,
            'wilaya': wilaya,
            'blood_group': blood_group,
            'status': status,
            'statement_id': statement_id,
            'statement_created_at': statement_created_at
        })

    return render_template('dashboard.html', reports=reports)

@app.route('/statement_details/<int:statement_id>')
def statement_details(statement_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM statements WHERE id = ?", (statement_id,))
    statement = c.fetchone()
    
    if statement is None:
        conn.close()
        None
        return jsonify({'error': 'Statement not found'}), 404

    c.execute("SELECT image_path, full_name FROM reports WHERE id = ?", (statement[6],))
    report = c.fetchone()
    report_image_path = report[0] if report else None
    missing_person_name = report[1] if report else "Unknown"
    
    conn.close()

    match_verified = False
    match_confidence = None
    if statement[4] and report_image_path:  # statement[4] is image_path
        try:
            result = DeepFace.verify(statement[4], report_image_path, model_name="Facenet")
            match_verified = result['verified']
            match_confidence = result['distance']
            print(f"Face match result for statement {statement_id}: {result}")
        except Exception as e:
            None
    return jsonify({
        'statement_id': statement[0],
        'reporter_full_name': statement[1],
        'phone_number': statement[2],
        'id_number': statement[3],
        'image_path': statement[4] if statement[4] else "No image available",
        'other_details': statement[5] if statement[5] else "No additional details",
        'related_report_id': statement[6],
        'created_at': statement[7],
        'missing_person_name': missing_person_name,
        'match_verified': match_verified,
        'match_confidence': match_confidence
    })

@app.route('/update_status/<int:report_id>/<status>')
def update_status(report_id, status):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE reports SET status = ? WHERE id = ?", (status, report_id))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/report_details/<int:report_id>')
def report_details(report_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
    report = c.fetchone()
    conn.close()
    if report:
        return jsonify({
            'full_name': report[1], 'birthdate': report[2], 'gender': report[3],
            'missing_date': report[4], 'wilaya': report[5], 'blood_group': report[6],
            'other_details': report[7], 'reporter_full_name': report[8],
            'phone_number': report[9], 'id_number': report[10], 'image_path': report[11],
            'status': report[12]
        })
    return jsonify({'error': 'Report not found'}), 404

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
