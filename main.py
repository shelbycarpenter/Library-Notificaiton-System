from flask import jsonify, Flask

from app import functions # Import the whole functions module
from app.functions import connect_db, fetch_new_books, get_patron_data, match_books_to_patrons, generate_email_content, \
    send_email_notification, update_email_sent_history, close_db_connection

app = Flask(__name__)

API_URL = "https://api.gapines.org/new-arrivals"


@app.route('/send_notifications', methods=['GET'])
def send_notifications():
    # Connect to the database
    conn = connect_db()
    if not conn:
        return jsonify({"status": "error", "message": "Failed to connect to the database"}), 500

    # Fetch new books from GA PINES API
    new_books = fetch_new_books(API_URL)
    if not new_books:
        return jsonify({"status": "error", "message": "Failed to fetch new books"}), 500

    # Fetch patron data and preferences
    patrons = get_patron_data(conn)
    if not patrons:
        return jsonify({"status": "error", "message": "Failed to fetch patron data"}), 500

    # Process each patron
    for patron in patrons:
        patron_id, patron_name, patron_email, checkout_history = patron

        # Match books to the patron's interests
        matched_books = match_books_to_patrons(new_books, checkout_history)
        if matched_books:
            # Generate email content
            email_content = generate_email_content(patron_name, matched_books)

            # Send the notification email
            send_email_notification(patron_email, "New Library Arrivals Based on Your Interests", email_content)

            # Update email sent history
            update_email_sent_history(conn, patron_id)

    # Close database connection
    close_db_connection(conn)

    return jsonify({"status": "success", "message": "Notifications sent successfully"}), 200


if __name__ == "__main__":
    app.run(debug=True)

