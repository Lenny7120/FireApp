from flask import Flask, render_template, request, redirect, url_for, g
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import sqlite3
from geopy.geocoders import Nominatim
import requests


app = Flask(__name__, static_url_path='/static')
app.secret_key = 'Treysongz78'


login_manager = LoginManager(app)
login_manager.login_view = 'login'


DATABASE = 'user_database.db'


class User(UserMixin):
    def __init__(self, user_id, username):
        self.id = user_id
        self.username = username


class FireApp:
    def create_connection(self):
        return sqlite3.connect(DATABASE)
        

    def close_connection(self, connection):
        if connection:
            connection.close()
        

    def create_user_table(self):
        conn = self.create_connection()
        cursor = conn.cursor()

        cursor.execute('''
             CREATE TABLE IF NOT EXISTS users(
             id INTEGER  PRIMARY KEY AUTOINCREMENT,
             username TEXT NOT NULL,
             password TEXT NOT NULL,
             email  TEXT NOT NULL,
             phone_number  TEXT NOT NULL
             )
             ''')

        conn.commit()
        conn.close()


    def recreate_user_table(self):
        conn = None
        try :
            conn = self.create_connection()
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS users")
            self.create_user_table()
            conn.commit()
        except sqlite3.Error as e:
            print(f"SQlite error: {e}")
        finally:
            self.close_connection(conn)

    def inspect_table_structure(self):
        conn = self.create_connection()
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()

        for column in columns:
            print(columns)

        conn.close()

    def get_user_location(self):
        if request.endpoint == 'report':
            geolocator = Nominatim(user_agent="FireApp")
            user_ip = request.remote_addr
            location = geolocator.geocode(user_ip)

            if location:
                return f"{location.latitude} {location.longitude}"
            else:
                return "Location not available"
        return None

    def sent_to_organization(self, username, emergency_type, user_location):
        organization_server_url = "https://example.com/organization-api"

        data = {
                'username': username,
                'emergency_type': emergency_type,
                'user_location': user_location
                }
        try:
            response = request.post(organization_server_url, json=data)
            if response.satus_code == 200:
                print("Data sent to organization sucessfully.")
            else:
                print(f"Failed to send data. Server status code {response.status_code}.")
        except requests.exceptions.RequestExceptions as e:
            print(f"An error occured while sending data: {e}")

    def register_user(self, username, password, email, phone_number):
        print(f"Registering user: {username}, {password}, {email}, {phone_number}")
        conn = self.create_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users(username, password, email, phone_number)
            VALUES(?, ?, ?, ?)
            ''', (username, password, email, phone_number))
        conn.commit()
        conn.close()

    def verify_login(self, username, password):
        conn = self.create_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM users WHERE username=? AND password=?
        ''', (username, password))
        user = cursor.fetchone()
        conn.close()
        return user

    def handle_registration(self, username, password, email, phone_number):
        self.register_user(username, password, email, phone_number)
        print("User registered successfully.")


fire_app = FireApp()
fire_app.recreate_user_table()
fire_app.inspect_table_structure()


@login_manager.user_loader
def load_user(user_id):
    with fire_app.create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id))
        user_data = cursor.fetchone()
        if user_data:
            return User(user_data[0], user_data[1])
    return None


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with fire_app.create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?',(username,))
            user_data = cursor.fetchone()
            if user_data:
                user = User(user_data[0], user_data[1])
                login_user(user)
                return redirect(url_for('report'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        print("RECIVED POST request")
        print("Form Data:", request.get_data(as_text=True))
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')

        if username is not None:
            fire_app.handle_registration(username, password, email, phone_number)
        return redirect(url_for('login'))
        
    else:
        print("Username not found in form data")

    return render_template('register.html')


@app.route('/report', methods=['GET', 'POST'])
@login_required
def report():
    if request.method == 'POST':
        return redirect(url_for('home'))

    return render_template('report.html', username=current_user.username, user_location=fire_app.get_user_location())


if __name__ == '__main__':
    app.run(debug=True)
