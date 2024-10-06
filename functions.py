import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import psycopg2
from datetime import datetime
import requests
from flask import jsonify

# Function to connect to the PostgreSQL database
def connect_db():
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="library_system",
            user="library_admin",
            password="password"
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

# Function to fetch new book data from GA PINES API
def fetch_new_books(api_url):
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except Exception as e:
        print(f"Error fetching data from GA PINES: {e}")
        return []

# Function to fetch patron data and preferences from the database
def get_patron_data(conn):
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name, email, checkout_history FROM patrons WHERE notification_opt_in = TRUE;")
        patrons = cur.fetchall()
        cur.close()
        return patrons
    except Exception as e:
        print(f"Error fetching patron data: {e}")
        return []

# Function to find books matching patrons' interests based on checkout history
def match_books_to_patrons(new_books, checkout_history):
    matched_books = [book for book in new_books if any(item in book['genre'] for item in checkout_history)]
    return matched_books

# Function to generate email content based on matched books
def generate_email_content(patron_name, matched_books):
    content = f"Hi {patron_name},\n\nBased on your checkout history, here are some new arrivals at the library that you may be interested in:\n"
    for book in matched_books:
        content += f"- {book['title']} by {book['author']} (Genre: {book['genre']})\n"
    content += "\nHappy reading!\n\nBest regards,\nYour Library Team"
    return content

# Function to send email notifications to patrons
def send_email_notification(patron_email, subject, content):
    try:
        sender_email = "your_email@example.com"
        sender_password = "your_password"

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = patron_email
        msg['Subject'] = subject

        msg.attach(MIMEText(content, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print(f"Email sent to {patron_email}")
    except Exception as e:
        print(f"Error sending email to {patron_email}: {e}")

# Function to update the email sent history in the database
def update_email_sent_history(conn, patron_id):
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO email_notifications (patron_id, sent_time) VALUES (%s, %s)",
            (patron_id, datetime.now())
        )
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"Error updating email history: {e}")

# Close database connection
def close_db_connection(conn):
    if conn:
        conn.close()
