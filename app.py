import os
from flask import Flask, request, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session



# Initialize Flask App
app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'  # Change to a random secret key

# File Upload Configuration
UPLOAD_FOLDER = '/static/uploads'  # Change to your desired upload folder path
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = "/static/uploads"

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

#GUI to display the the users registered
@app.route('/users')
def show_users():
    users = User.query.all()
    return render_template('users.html', users=users)


@app.route('/register', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        plain_text_password = request.form['password']
        hashed_password = generate_password_hash(plain_text_password)
        name = request.form['name']
        contact = request.form['contact']

        # Optionally handle file upload
        # if 'profile-pic' in request.files:
        #     file = request.files['profile-pic']
        #     if file.filename != '':
        #         filename = secure_filename(file.filename)
        #         file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        #         # Update new_user to include the image path

        new_user = User(email=email, password=hashed_password, name=name, contact=contact)
        db.session.add(new_user)
        db.session.commit()

        # Redirect to the login page after successful registration
        return redirect(url_for('login'))  # Replace 'login' with your login view function name
    return render_template('register.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print("Username:", username)
        print("Password:", password)
        user = User.query.filter_by(email=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id  # Storing user's id in the session
            session['username'] = user.name  # Storing user's name in the session
            print("LOGIN WORKED")
            return redirect(url_for('home'))
    
        else:
            print("didnt work")
            return render_template('login.html', error="Invalid username or password")

    return render_template('login.html')




@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))  # or redirect to home



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
@app.route('/')
def home():
    # featured_items = User.query.filter(User.image_url != None).all()
    # return render_template('LandingPage.html', featured_items=featured_items)
    return render_template('LandingPage.html')


# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



# Start the Flask application
if __name__ == '__main__':
    app.run(debug=True)
