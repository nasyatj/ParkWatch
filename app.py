import os

from google.cloud import storage #importing google cloud
from dotenv import load_dotenv

from flask import Flask, render_template, request, redirect, url_for, session
from flask import send_from_directory
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename

from database import *

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
bcrypt = Bcrypt(app)

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
#path to google crednetials

BUCKET_NAME = "reported_pictures"
#bucket name

def upload_to_gcs(file, filename):
    
    #Upload file to bucket
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"uploads/{filename}")

    #Upload File
    blob.upload_from_file(file)
    return blob.public_url


@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    active_tab = request.args.get('tab', 'maintenance-tab')

    search = request.args.get('search', '').strip().lower()
    weather = get_latest_weather()
    tasks = get_tasks()
    reports = get_reports()
    parks = get_parks()

    # Apply filtering
    if search:
        reports = [
        report for report in reports
        if search in report[0].lower()
        or search in report[1].lower()
        or search in report[4].lower()
    ]


    # Chart data prep
    type_counts = Counter([report[1] for report in reports])    # Report Type
    status_counts = Counter([report[4] for report in reports])  # Report Status
    park_counts = Counter([report[0] for report in reports])    # Park Name
    task_counts = get_task_summary(tasks, parks)                # Maintenance per Park (using park name)

    return render_template(
        'dashboard.html',
        weather=weather,
        reports=reports,
        tasks=tasks,
        username=session['username'],
        role=session['role'],
        type_counts=dict(type_counts),
        status_counts=dict(status_counts),
        park_counts=dict(park_counts),
        task_counts=dict(task_counts),  
        active_tab=active_tab,
        parks = parks
    )


@app.route('/submit_report', methods=['POST'])
def submit_report():
    park = request.form.get('park')
    report_type = request.form.get('report_type')
    details = request.form.get('details')
    photo_file = request.files.get('photo')
    photo_filename = None

    if photo_file and photo_file.filename != '':
        photo_filename = secure_filename(photo_file.filename)

        # Save locally
        local_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
        photo_file.save(local_path)

        # Upload to GCS
        upload_to_gcs(open(local_path, 'rb'), photo_filename)

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO park_reports (park, report_type, details, photo, date, status) VALUES (%s, %s, %s, %s, CURRENT_DATE, 'Pending')",
            (park, report_type, details, photo_filename)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Error inserting report:", e)

    active_tab = request.form.get('active_tab', 'reports-tab')
    return redirect(url_for('home', tab=active_tab))



@app.route('/resolve_report', methods=['POST'])
def resolve_report():
    report_id = request.form.get('report_id')
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE park_reports SET status = 'Resolved' WHERE id = %s", (report_id,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Error updating report status:", e)
    return redirect(url_for('home'))


@app.route('/delete_report', methods=['POST'])
def delete_report():
    if session.get('role') != 'admin':
        return "Unauthorized", 403

    report_id = request.form.get('report_id')
    active_tab = request.form.get('active_tab', 'maintenance-tab')

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT photo FROM park_reports WHERE id = %s", (report_id,))
        photo = cur.fetchone()[0]
        cur.execute("DELETE FROM park_reports WHERE id = %s", (report_id,))
        conn.commit()
        cur.close()
        conn.close()

        if photo:
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo)
            if os.path.exists(photo_path):
                os.remove(photo_path)
    except Exception as e:
        print("Error deleting report:", e)

    return redirect(url_for('home', tab=active_tab))

@app.route('/add_task', methods=['POST'])
def add_task():
    if session.get('role') != 'admin':
        return "Unauthorized", 403

    park = request.form['park']
    task = request.form['task']
    date = request.form['date']

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO maintenance_tasks (park, task, date) VALUES (%s, %s, %s)",
            (int(park), task, date)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Error inserting task:", e)

    return redirect(url_for('home', tab='maintenance-tab', selected_park=park))


@app.route('/delete_task', methods=['POST'])
def delete_task():
    if session.get('role') != 'admin':
        return "Unauthorized", 403

    task_id = request.form.get('task_id')
    active_tab = request.form.get('active_tab', 'maintenance-tab')

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM maintenance_tasks WHERE id = %s", (task_id,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Error deleting task:", e)

    return redirect(url_for('home', tab=active_tab))

def get_task_summary(tasks, parks):
    park_id_to_name = {park[0]: park[1] for park in parks}
    task_counts = {}

    for task in tasks:
        park_id = task[3]
        park_name = park_id_to_name.get(park_id, None)
        if park_name:
            task_counts[park_name] = task_counts.get(park_name, 0) + 1
        # else skip unknown parks

    return task_counts


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, password, role FROM users WHERE username = %s", (username,))
            user = cur.fetchone()
            cur.close()
            conn.close()

            if user and bcrypt.check_password_hash(user[1], password):
                session['user_id'] = user[0]
                session['username'] = username
                session['role'] = user[2]
                return redirect(url_for('home'))
            else:
                return "Invalid credentials", 401
        except Exception as e:
            return f"Login error: {e}"

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('login'))
        except Exception as e:
            return f"Registration error: {e}"

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))




@app.route('/download/<filename>')
def download_photo(filename):
    if 'role' not in session or session['role'] != 'admin':
        return "Unauthorized", 403

    try:
        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
    except Exception as e:
        return f"Error downloading file: {e}", 500


@app.route('/add_park', methods=['POST'])
def add_park():
    if session.get('role') != 'admin':
        return "Unauthorized", 403

    park_name = request.form.get('park_name')

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO parks (park_name) VALUES (%s)", (park_name,))
        conn.commit()
        cur.close()
        conn.close()
        print("New park added:", park_name)
    except Exception as e:
        print("Error adding park:", e)

    return redirect(url_for('home', tab='maintenance-tab'))



# -------------------- Run App --------------------
if __name__ == '__main__':
    app.run(debug=True)
