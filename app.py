from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from geopy.geocoders import Nominatim
import requests


app = Flask(__name__, static_url_path='/static')


class FireApp:
    def __init__(self):
        self.create_user_table()

    def create_connection(self):
        return sqlite3.connect("user_database.db")

    def create_user_table(self):
        conn = self.create_connection()
        cursor = conn.cursor()

        cursor.execute('''
             CREATE TABLE IF NOT EXISTS users(
             id INTEGER  PRIMARY KEY AUTOINCREMENT,
             username TEXT NOT NULL,
             password TEXT NOT NULL,
             emergency_type TEXT NOT NULL,
             location TEXT NOT NULL
             )
             ''')

        conn.commit()
        conn.close()

    def get_user_location(self):
        geolocator = Nominatim(user_agent="FireApp")
        user_ip = request.remote_addr
        location = geolocator.geocode(user_ip)

        if location:
            return f"{location.latitude} {location.longitude}"
        else:
            return "Location not available"

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

    def register_user(self, username, password, emergency_type, user_location):
        conn = self.create_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users(username, password, emergency_type, location)
            VALUES(?, ?, ?, ?)
            ''', (username, password, emergency_type, user_location))
        conn.commit()
        conn.close()

    def handle_registration(self, username, password, emergency_type, user_location):
        self.register_user(username, password, emergency_type, user_location)
        self.send_to_organization(username, password, emergency_type, user_location)


fire_app = FireApp()


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        emergency_type = request.form['emergency_type']
        user_location = request.form['user_location']

        fire_app.handle_registration(username, password, emergency_type, user_location)
        return redirect(url_for('home'))

    return render_template('register.html', user_location=fire_app.get_user_location())


if __name__ == '__main__':
    app.run(debug=True)
