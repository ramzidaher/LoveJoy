import os
from flask import Flask, request, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

# Initialize Flask App
app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'  # Change to a random secret key

# File Upload Configuration
UPLOAD_FOLDER = 'path/to/upload/folder'  # Change to your desired upload folder path
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(20), nullable=True)
    image_url = db.Column(db.String(300), nullable=True)  # Field to store image path

    def __repr__(self):
        return f'<User {self.name}>'

# Create the database tables before the first request
@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/users')
def show_users():
    users = User.query.all()
    return render_template('users.html', users=users)

# Route for the registration form
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']  # In production, hash this password
        name = request.form['name']
        contact = request.form['contact']

        new_user = User(email=email, password=password, name=name, contact=contact)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('signup'))
    return render_template('signup.html')

# Route for login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(email=username).first()
        if user and user.password == password:
            session['username'] = user.name
            return redirect(url_for('home'))
        else:
            return "Invalid login"

    return render_template('login.html')

# Route for file upload
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            user = User.query.filter_by(name=session['username']).first()
            user.image_url = filename
            db.session.commit()
            return redirect(url_for('home'))

    return render_template('upload.html')

# Route for displaying home page with uploaded items
@app.route('/home')
def home():
    featured_items = User.query.filter(User.image_url != None).all()
    return render_template('home.html', featured_items=featured_items)

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



# Start the Flask application
if __name__ == '__main__':
    app.run(debug=True)
