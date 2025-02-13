import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

# Initialize Flask app and configure SQLite database
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///missing_people.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)

# Create database model for reports
class MissingPersonReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255), nullable=False)
    birthdate = db.Column(db.String(10), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    missing_date = db.Column(db.String(10), nullable=False)
    blood_group = db.Column(db.String(5), nullable=False)
    image = db.Column(db.String(100), nullable=True)  # Store image path
    other_details = db.Column(db.String(500), nullable=True)
    reporter_full_name = db.Column(db.String(255), nullable=False)
    reporter_phone_number = db.Column(db.String(20), nullable=False)
    reporter_id_number = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='Pending')  # Pending, Accepted, Rejected

# User model for login system
class User(UserMixin):
    id = 1
    username = "admin"
    password = "admin"  # hardcoded for simplicity

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User()

# Home page
@app.route('/')
def home():
    return render_template('home.html')

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == "admin" and password == "admin":  # Static login
            login_user(User())  # Log in as the admin user
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials, please try again.")
    return render_template('login.html')

# Logout page
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# Dashboard page - View and manage reports
@app.route('/dashboard')
@login_required
def dashboard():
    reports = MissingPersonReport.query.all()
    return render_template('dashboard.html', reports=reports)

# Report page - Submit a new missing person report
@app.route('/report', methods=['GET', 'POST'])
def report():
    if request.method == 'POST':
        full_name = request.form['full_name']
        birthdate = request.form['birthdate']
        gender = request.form['gender']
        missing_date = request.form['missing_date']
        blood_group = request.form['blood_group']
        image = request.form['image']
        other_details = request.form['other_details']
        reporter_full_name = request.form['reporter_full_name']
        reporter_phone_number = request.form['reporter_phone_number']
        reporter_id_number = request.form['reporter_id_number']

        new_report = MissingPersonReport(
            full_name=full_name,
            birthdate=birthdate,
            gender=gender,
            missing_date=missing_date,
            blood_group=blood_group,
            image=image,
            other_details=other_details,
            reporter_full_name=reporter_full_name,
            reporter_phone_number=reporter_phone_number,
            reporter_id_number=reporter_id_number,
        )
        db.session.add(new_report)
        db.session.commit()
        flash("Report submitted successfully!")
        return redirect(url_for('dashboard'))
    return render_template('report.html')

# Accept or reject a report
@app.route('/update_report/<int:id>/<status>')
@login_required
def update_report(id, status):
    report = MissingPersonReport.query.get(id)
    if report:
        report.status = status
        db.session.commit()
        flash(f"Report {status} successfully.")
    return redirect(url_for('dashboard'))

# Initialize the database (run once)
@app.before_first_request
def create_tables():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
