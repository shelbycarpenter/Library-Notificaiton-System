import sqlite3
import requests
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

# Function to connect to the SQLite database
def connect_db():
    try:
        conn = sqlite3.connect('library_notification_system.db')
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

# Function to close the database connection
def close_db_connection(conn):
    if conn:
        conn.close()

# Function to fetch new books from GA PINES API
def fetch_new_books(api_url):
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            new_books = response.json()  # Assuming the API returns JSON
            return new_books
        else:
            print(f"Failed to fetch new books. Status code: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching new books: {e}")
        return []

# Function to fetch patron data and preferences from the database
def get_patron_data(conn):
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT PatronID, Name, Email, Preferences, NotificationFrequency, CommunicationChannel
            FROM Patrons
            WHERE NotificationOptIn = 1
        """)
        patrons = cur.fetchall()
        cur.close()
        return patrons
    except Exception as e:
        print(f"Error fetching patron data: {e}")
        return []

# Function to match books to patrons based on preferences
def match_books_to_patrons(new_books, patron_preferences):
    matched_books = []
    preferences = patron_preferences.split(', ')  # Assuming preferences are comma-separated genres
    for book in new_books:
        if book['genre'] in preferences:
            matched_books.append(book)
    return matched_books

# Function to generate email content
def generate_email_content(patron_name, matched_books):
    book_list = ''
    for book in matched_books:
        book_list += f"- {book['title']} by {book['author']}\n"
    email_content = f"Hello {patron_name},\n\nBased on your interests, we thought you'd like these new arrivals:\n\n{book_list}\nHappy reading!\nYour Library Team"
    return email_content

# Function to send email notifications
def send_email_notification(to_email, subject, content):
    # Email configuration
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = 'your_email@gmail.com'  # Replace with your email
    smtp_password = 'your_password'         # Replace with your email password

    # Create the email message
    msg = MIMEText(content)
    msg['Subject'] = subject
    msg['From'] = smtp_username
    msg['To'] = to_email

    try:
        # Connect to SMTP server and send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Error sending email to {to_email}: {e}")

# Function to update email sent history in the database
def update_email_sent_history(conn, patron_id):
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Notifications (PatronID, NotificationDate) VALUES (?, ?)",
            (patron_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"Error updating email history: {e}")

