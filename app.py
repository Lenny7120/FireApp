from flask import Flask, render_template, request, redirect, url_for 
import sqlite3
from geopy.geocoders import Nominatim
import request


app = Flask(__name__)


class FireApp:
    def __init__(self):
        self.create_user_table()

    def create_connection(self):
        return sqlite3.connect"user_database.db")

    def create_user_table(self):
        conn = self.create_connection()
        cursor = conn.cursor()

        cursor.execute('''
             CREATE TABLE IF NOT EXISTS users(
             id PRIMARY KEY AUTOINCREMENT,
             username TEXT NOT NULL,
             password TEXT NOT NULL,
             emergency_type TEXT NOT NULL,
             location TEXT NOT NULL
             )
             ''')

        conn.commit()
        conn.close()

    def get_user_location(self):
        geolocator = Nominatim(user_agent = "FireApp")
        user_ip = request.remote_addr
        location = geolocator.geocode(user_ip)

        if location:
            return f"{location.latitude} {location.longitude}"
        else:
            rwturn "Location not available"

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
                print(f"Failed to send data. Server responded with status code {response.status_code}.")
