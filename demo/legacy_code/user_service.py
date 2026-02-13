"""
Legacy User Service - Flask synchronous implementation
This file contains hardcoded credentials and should be BLOCKED by the scanner
"""

from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Hardcoded API key - SECURITY VIOLATION
API_KEY = "sk_live_51HxKj2eZvKYlo2C9x8rT3mN4pQ7wX6vU5yR8sA1bZ"

# Hardcoded database password - SECURITY VIOLATION
DB_PASSWORD = "supersecretpassword123"


class UserService:
    def __init__(self):
        self.db_connection = self.connect_to_database()

    def connect_to_database(self):
        """Connect to database using hardcoded credentials"""
        # This is legacy code with hardcoded credentials
        connection_string = f"postgresql://admin:{DB_PASSWORD}@localhost/userdb"
        print(f"Connecting with: {connection_string}")
        return sqlite3.connect('users.db')

    def get_user(self, user_id):
        """Synchronous user retrieval - legacy pattern"""
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        return result

    def create_user(self, username, email):
        """Synchronous user creation"""
        cursor = self.db_connection.cursor()
        cursor.execute(
            "INSERT INTO users (username, email) VALUES (?, ?)",
            (username, email)
        )
        self.db_connection.commit()
        return cursor.lastrowid

    def update_user(self, user_id, data):
        """Update user data"""
        cursor = self.db_connection.cursor()
        cursor.execute(
            "UPDATE users SET username = ?, email = ? WHERE id = ?",
            (data.get('username'), data.get('email'), user_id)
        )
        self.db_connection.commit()


@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user_endpoint(user_id):
    """Flask route for getting user - synchronous"""
    # Verify API key
    if request.headers.get('X-API-Key') != API_KEY:
        return jsonify({'error': 'Unauthorized'}), 401

    service = UserService()
    user = service.get_user(user_id)

    if user:
        return jsonify({
            'id': user[0],
            'username': user[1],
            'email': user[2]
        })
    else:
        return jsonify({'error': 'User not found'}), 404


@app.route('/api/users', methods=['POST'])
def create_user_endpoint():
    """Flask route for creating user - synchronous"""
    if request.headers.get('X-API-Key') != API_KEY:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    service = UserService()
    user_id = service.create_user(data['username'], data['email'])

    return jsonify({'id': user_id, 'message': 'User created'}), 201


if __name__ == '__main__':
    app.run(debug=True, port=5000)
