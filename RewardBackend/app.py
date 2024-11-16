import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Folder for storing uploaded face images
KNOWN_FACES_FOLDER = 'static/known_faces'
if not os.path.exists(KNOWN_FACES_FOLDER):
    os.makedirs(KNOWN_FACES_FOLDER)

app.config['UPLOAD_FOLDER'] = KNOWN_FACES_FOLDER

# Initialize or connect to the database
def init_db():
    conn = sqlite3.connect('club_users.db')
    c = conn.cursor()
    # Adding a column for the image path
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT,
                    contact TEXT,
                    image_path TEXT,
                    points INTEGER DEFAULT 0
                 )''')
    conn.commit()
    conn.close()

init_db()

# Function to generate user names like "person_1", "person_2", etc.
def generate_username():
    conn = sqlite3.connect('club_users.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM users')
    count = c.fetchone()[0] + 1
    conn.close()
    return f"person_{count}"

@app.route('/')
def index():
    return render_template('index.html')

# Route to handle user registration
@app.route('/register', methods=['POST'])
def register():
    # Generate a default username like "person_1", "person_2"
    username = generate_username()
    file = request.files['image']

    if file:
        filename = f"{username}.jpg"  # Save the image with username
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(image_path)  # Save image to known_faces folder

        # Insert new user with auto-generated name and image path
        conn = sqlite3.connect('club_users.db')
        c = conn.cursor()
        c.execute('INSERT INTO users (name, image_path) VALUES (?, ?)',
                  (username, image_path))
        conn.commit()
        conn.close()

    return redirect(url_for('dashboard'))

# Admin dashboard to display all users
@app.route('/dashboard')
def dashboard():
    conn = sqlite3.connect('club_users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users')
    users = c.fetchall()
    conn.close()
    return render_template('dashboard.html', users=users)

# Route to edit user details
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_user(id):
    conn = sqlite3.connect('club_users.db')
    c = conn.cursor()

    if request.method == 'POST':
        # Get updated information from the form
        name = request.form['name']
        email = request.form['email']
        contact = request.form['contact']
        c.execute('UPDATE users SET name = ?, email = ?, contact = ? WHERE id = ?',
                  (name, email, contact, id))
        conn.commit()
        return redirect(url_for('dashboard'))

    c.execute('SELECT * FROM users WHERE id = ?', (id,))
    user = c.fetchone()
    conn.close()

    return render_template('edit_user.html', user=user)

# Route to delete user
@app.route('/delete/<int:id>')
def delete_user(id):
    conn = sqlite3.connect('club_users.db')
    c = conn.cursor()
    c.execute('DELETE FROM users WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

# Route to increase or decrease points
@app.route('/update_points/<int:id>', methods=['POST'])
def update_points(id):
    points = int(request.form['points'])
    conn = sqlite3.connect('club_users.db')
    c = conn.cursor()
    c.execute('UPDATE users SET points = points + ? WHERE id = ?', (points, id))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
