import os
from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session
from datetime import datetime
from flask import flash, redirect, url_for
from datetime import timedelta
from sqlalchemy import create_engine, MetaData, Table







# Initialize Flask App
app = Flask(__name__)


# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'  # Change to a random secret key

# File Upload Configuration
UPLOAD_FOLDER = 'static/uploads'  
UPLOAD_FOLDER_PROFILE = 'static/uploads/profilepics'
UPLOAD_FOLDER_EVALUATION = 'static/uploads/evaluation'


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_FOLDER_PROFILE'] = UPLOAD_FOLDER_PROFILE
app.config['UPLOAD_FOLDER_EVALUATION'] = UPLOAD_FOLDER_EVALUATION


app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB


# Initialize SQLAlchemy
db = SQLAlchemy(app)

#All classes#

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(20), nullable=True)
    image_url = db.Column(db.String(300), nullable=True) 
    image_data = db.Column(db.LargeBinary)  

    def __repr__(self):
        return f'<User {self.name}>'

# Antique Evaluation
class Antique(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    age = db.Column(db.Integer, nullable=True)
    origin = db.Column(db.String(100), nullable=True)
    condition = db.Column(db.String(100), nullable=True)
    image_url = db.Column(db.String(300), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    owner = db.relationship('User', backref=db.backref('antiques', lazy=True))

    def __repr__(self):
        return f'<Antique {self.name}>'


@app.before_first_request
def create_tables():
    db.create_all()

# Create the database tables before the first request# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#Main route page (landingpage)
@app.route('/')
def home():
    return render_template('LandingPage.html')

@app.route('/register', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        plain_text_password = request.form['password']
        hashed_password = generate_password_hash(plain_text_password)
        name = request.form['name']
        contact = request.form['contact']
        # profile_url = request.form['file']

        profile_pic = request.files.get('profile-pic')
        if profile_pic and allowed_file(profile_pic.filename):
            filename = secure_filename(profile_pic.filename)
            profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER_PROFILE'], filename))

            # URL to access the image (adjust based on your static URL configuration)
            profile_pic_url = url_for('static', filename='uploads/profilepics/' + filename)
        else:
            profile_pic_url = None  # Or a default image path
        new_user = User(email=email, password=hashed_password, name=name, contact=contact, image_url=profile_pic_url)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))  
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember_me = request.form.get('remember_me')  
        
        user = User.query.filter_by(email=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.name

        
            if remember_me:
                session.permanent = True
                app.permanent_session_lifetime = timedelta(days=30) 

            return redirect(url_for('profiledb'))
        else:
            return render_template('login.html', error="Invalid username or password")

    return render_template('login.html')

#Logs out the userand ends session
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/evaluation', methods=['GET', 'POST'])
def evaluateAntique():           
    if 'user_id' not in session:
        return render_template('login.html')
    
    current_user_id = session['user_id']
    current_user = User.query.filter_by(id=current_user_id).first()
    if not current_user:
        # Handle case where current_user is not found
        flash("User not found.", "error")
        return redirect(url_for('login'))  # Redirect to login page

    if request.method == 'POST':
        anti_name = request.form['antique_name']
        anti_description = request.form['antique_description']
        anti_age = request.form['antique_est_age']

        # Handle file upload
        antique_image = request.files['antique_image']
        if antique_image.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)

        if antique_image and allowed_file(antique_image.filename):
            filename = secure_filename(antique_image.filename)
            antique_image.save(os.path.join(app.config['UPLOAD_FOLDER_EVALUATION'], filename))

            # Create and save the Antique object
            new_antique = Antique(
                name=anti_name,
                description=anti_description,
                age=anti_age,
                image_url=filename,
                user_id=current_user_id  # Set the user_id field
            )
            db.session.add(new_antique)
            db.session.commit()
            flash("Antique successfully uploaded for evaluation!", "success")
            return render_template('antiquebeingevaluated.html')
        else:
            flash('Invalid file type', 'error')

    return render_template('evaluation.html')



@app.route('/profile', methods=['GET', 'POST'])
def profiledb():
    
     # Redirect to LandingPage if not logged in
    if 'user_id' not in session:
        return redirect(url_for('home')) 
    
    # Initialize variables
    name = email = tel = None
    current_user_antiques = []

    if 'user_id' in session:
        current_user_id = session['user_id']
        current_user = User.query.filter_by(id=current_user_id).first()

        if current_user:
            # Set user details
            name = current_user.name  
            email = current_user.email
            tel = current_user.contact
            # Get antiques associated with the current user
            current_user_antiques = Antique.query.filter_by(user_id=current_user_id).all()
            image_url = current_user.image_url

            if len(current_user_antiques) > 0:
                print("The list has items.")
            else:
                print("The list is empty.")
    return render_template('userdb.html', phonenumber=tel, emailaddr=email,username=name, current_user_antiques=current_user_antiques, image_url=image_url)











# Start the Flask application
if __name__ == '__main__':
    app.run(debug=True)