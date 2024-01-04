from flask import Flask, render_template, request, redirect, url_for, g
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import sqlite3
from geopy.geocoders import Nominatim
import requests
import datetime


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
    def __init__(self):
        self.create_user_table()


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


    def get_daily_safety_tips():
        print("Inside get_daily_safety_tips function")
        tips = [
            "Don't overload electrical sockets.",
            "Turn off your vehicle's engine when refuelling.",
            "Keep petrol and other fuels out of sight and reach of children. Petrol is highly toxic in addition to being a fire hazard.",
            "Don't smoke, light matches or use lighters while refueling.",
            "Don't use any electronic device,such as cell phones while refueling.",
            "To avoid spills, do not overfill your vehicle.",
            "If a fire starts while you are refueling, do not remove the nozzle from the vehicle or try to stop the flow of fuel. Leave the area immediately and call for help.",
            "if you must get into the vehicle during refueling, discharge any static electricity by touching metal on the outside of the nozzle is removed from your vehicle tank inlet.",
            "Use only approved portable containers for transporting or storing petrol.",
            "Keep matches away from children.",
            "Turn off all electrical socket when not in use",
            "Change rubber seal regularly when filling your gas.",
            "Use qualified electrician when wiring your house.",
            "when percieve the smell of gas in your kitchen, open the windows and doors to allow fresh air in, Don't turn on the lights or use your phone."
        ]

        today = datetime.date.today().day
        result = tips[today % len(tips)]
        print("Daily safety tips:", result)



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
    print("inside /report route")
    if request.method == 'POST':
        user_location = fire_app.get_user_location()
        daily_safety_tip = get_daily_safety_tips()
        print("Daily Safety Tip:", daily_safety_tip)
        return render_template('report.html', username=current_user.username, user_location=user_location, daily_safety_tip=daily_safety_tip, show_popup=True)

    return render_template('report.html', username=current_user.username, user_location=fire_app.get_user_location(), show_popup=True)


if __name__ == '__main__':
    app.run(debug=True)
