import os
import click
from datetime import datetime, timedelta
from PIL import Image

from flask import (
    Flask, flash, redirect, render_template, request, session, url_for
)
from flask.cli import with_appcontext
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import create_engine, MetaData, Table
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from email_validator import validate_email, EmailNotValidError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
import imghdr
import pymemcache.client.hash
import logging
from logging.handlers import RotatingFileHandler



# Initialize Flask App
app = Flask(__name__)


# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/ramzidaher/Desktop/LoveJoy/instance/users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.secret_key = os.environ.get('2e2ccdcef15c5a71fd7ba1ffa6f3a3d0')
app.secret_key = '2e2ccdcef15c5a71fd7ba1ffa6f3a3d0'


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
# app.config['MAIL_USERNAME'] = os.environ.get('GMAIL_USERNAME')  # Set as environment variable
# app.config['MAIL_PASSWORD'] = os.environ.get('GMAIL_PASSWORD')  # Set as environment variable
# app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_USERNAME'] = 'ramzi.daher@gmail.com'  # Set as environment variable
app.config['MAIL_PASSWORD'] = 'vykn rhhe dpxw glsy'  # Set as environment variable
app.config['MAIL_DEFAULT_SENDER'] = 'ramzi.daher@gmail.com'


# Initialize limiter
limiter = Limiter(
    key_func=get_remote_address,  # Use the remote address of the client as the rate limit key
    app=app,
    default_limits=["200 per day", "50 per hour"]  # Default limits
)

# Initialize CSRF protection
csrf = CSRFProtect(app)


mail = Mail(app)




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

ALLOWED_MIME_TYPES = {'image/png', 'image/jpeg', 'image/gif'}


# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Setup logging
if not app.debug:
    file_handler = RotatingFileHandler('flask_app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Flask application startup')
    
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
    is_admin = db.Column(db.Boolean, default=False, nullable=False)


    def __repr__(self):
        return f'<User {self.name}>'

# Antique Evaluation
class Antique(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    request = db.Column(db.Text, nullable=True)
    age = db.Column(db.Integer, nullable=True)
    origin = db.Column(db.String(100), nullable=True)
    condition = db.Column(db.String(100), nullable=True)
    image_url = db.Column(db.String(300), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    owner = db.relationship('User', backref=db.backref('antiques', lazy=True))
    contact_method = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Pending')

    def __repr__(self):
        return f'<Antique {self.name}>'


##THIS GIVES ERROR## HAS BEEN REMOVED SO U CAN CREATE DB MANULALLY THROUGH CLI##
# @app.before_first_request
# def create_tables():
#     db.create_all()

# Create the database tables before the first request# Function to check allowed file extensions


#Main route page (landingpage)
@app.route('/')
def home():
    if 'user_id' not in session:
        return render_template('LandingPage.html')
    return redirect(url_for('homepage'))



def generate_reset_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='password-reset-salt')

def confirm_reset_token(token, expiration=1800):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=expiration)
    except:
        return False
    return email

@app.route('/register', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email'].strip()
                # Validate email format
                
        try:
            valid = validate_email(email)
            email = valid.email  # Update with the normalized form
        except EmailNotValidError:
            flash('Invalid email format', 'error')
            return redirect(url_for('signup'))
        
        # Check if the email is already registered
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered', 'error')
            return redirect(url_for('signup'))

        plain_text_password = request.form['password']
        hashed_password = generate_password_hash(plain_text_password)
        name = request.form['name']
        contact = request.form['contact']

        profile_pic = request.files.get('profile-pic')
        if profile_pic and allowed_file(profile_pic):                   
            filename = secure_filename(profile_pic.filename)
            profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER_PROFILE'], filename))
            profile_pic_url = url_for('static', filename='uploads/profilepics/' + filename)
        else:
            profile_pic_url = None  # Or a default image path

        new_user = User(email=email, password=hashed_password, name=name, contact=contact, image_url=profile_pic_url)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))  
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  # Limit to 5 requests per minute
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember_me = request.form.get('remember_me')  
        
        user = User.query.filter_by(email=username).first()
        if user:
            if check_password_hash(user.password, password):
                session['user_id'] = user.id
                session['username'] = user.name

                if remember_me:
                    session.permanent = True
                    app.permanent_session_lifetime = timedelta(days=30) 

                return redirect(url_for('homepage'))
            else:
                # Password doesn't match
                flash('Invalid password. Please try again.', 'error')
        else:
            # User not found
            flash('Email not registered. Please check your email or register.', 'error')

    return render_template('login.html')


#Logs out the userand ends session
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/evaluation', methods=['GET', 'POST'])
def evaluateAntique():    
    image_url = None  # Initialize image_url to a default value


    if 'user_id' not in session:
        return render_template('login.html')
    
    current_user_id = session['user_id']
    current_user = User.query.filter_by(id=current_user_id).first()
    if not current_user:
        flash("User not found.", "error")
        return redirect(url_for('login'))
    image_url = current_user.image_url
    if request.method == 'POST':
        anti_name = request.form['antique_name']
        anti_description = request.form['antique_description']
        request_anti = request.form['antique_request']
        anti_age = request.form['antique_est_age']
        preferred_method = request.form['preferred_contact_method']

        antique_image = request.files['antique_image']
        if not antique_image or antique_image.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
    
        if not allowed_file(antique_image):  # This is the correct check
            flash('Invalid file type or size', 'error')
            return redirect(request.url)
    
        filename = secure_filename(antique_image.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER_EVALUATION'], filename)
        antique_image.save(filepath)

        # Open the image and check dimensions
        with Image.open(filepath) as img:
            width, height = img.size

        max_width = 1024
        max_height = 1024

        if width > max_width or height > max_height:
            flash('Image dimensions exceed the allowed limit.', 'error')
            os.remove(filepath)  # Remove the saved image as it is not valid
            return redirect(request.url)

        # Create and save the Antique object
        new_antique = Antique(
            name=anti_name,
            description=anti_description,
            request=request_anti,
            age=anti_age,
            image_url=filename,
            user_id=current_user_id,
            contact_method=preferred_method,
            status='Pending'
        )


        db.session.add(new_antique)
        db.session.commit()
        flash("Antique successfully uploaded for evaluation!", "success")
        return render_template('antiquebeingevaluated.html')
    

    return render_template('evaluation.html', image_url=image_url)





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
            is_admin = current_user.is_admin
            # Get antiques associated with the current user
            current_user_antiques = Antique.query.filter_by(user_id=current_user_id).all()
            image_url = current_user.image_url

            if len(current_user_antiques) > 0:
                print("The list has items.")
            else:
                print("The list is empty.")
    return render_template('userdb.html', phonenumber=tel, emailaddr=email,username=name, current_user_antiques=current_user_antiques, image_url=image_url, is_admin=is_admin)



@app.route('/home')
def homepage():
    is_logged_in = 'user_id' in session
    image_url = None
    if is_logged_in:
        current_user_id = session['user_id']
        current_user = User.query.filter_by(id=current_user_id).first()
        image_url = current_user.image_url

    all_antiques = Antique.query.all()  # Fetching all antiques

    return render_template('homepage.html', image_url=image_url, is_logged_in=is_logged_in, all_antiques=all_antiques)



from flask import render_template

@app.route('/admin/')
def admin():
    if 'user_id' not in session or not User.query.get(session['user_id']).is_admin:
        return redirect(url_for('login'))

    # Retrieve all admin users and regular users
    admin_users = User.query.filter_by(is_admin=True).all()
    regular_users = User.query.filter_by(is_admin=False).all()

    # Counting admin users and regular users
    total_users = User.query.count()
    total_admins = len(admin_users)
    total_regular_users = len(regular_users)

    # Retrieve all antiques from the database and their respective user names
    antiques = Antique.query.all()

    # Create a dictionary to store user names by user ID
    user_names = {user.id: user.name for user in admin_users + regular_users}

    return render_template('admin.html', total_users=total_users, total_admins=total_admins, total_regular_users=total_regular_users, antiques=antiques, user_names=user_names)





@app.route('/admin/dashboard/users')
def admin_dashboard():
    if 'user_id' not in session or not User.query.get(session['user_id']).is_admin:
        return redirect(url_for('login'))

    users = User.query.all()
    
    admin_users = [user for user in users if user.is_admin]
    regular_users = [user for user in users if not user.is_admin]

    return render_template('admin_dashboard.html', admin_users=admin_users, regular_users=regular_users)



@app.route('/reset', methods=["GET", "POST"])
def reset_request():
    if request.method == "POST":
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            token = generate_reset_token(user.email)
            reset_url = url_for('reset_token', token=token, _external=True)
            msg = Message("Password Reset Request", 
            sender="your-email@example.com",
            recipients=[user.email])
            msg.body = f"To reset your password, visit the following link: {reset_url}"
            mail.send(msg)

            flash('A password reset email has been sent.', 'info')
        else:
            flash('Email does not exist.', 'warning')
    return render_template('reset_request.html')


@app.route('/reset/<token>', methods=["GET", "POST"])
def reset_token(token):
    if request.method == "POST":
        email = confirm_reset_token(token)
        if email:
            user = User.query.filter_by(email=email).first()
            user.password = generate_password_hash(request.form['password'])
            db.session.commit()
            flash('Your password has been updated!', 'success')
            print('Your password has been update')
            return redirect(url_for('login'))
        else:
            flash('That is an invalid or expired token', 'warning')
            return redirect(url_for('reset_request'))
    return render_template('reset_token.html')

@app.cli.command("promote-admin")
@click.argument("email")
@with_appcontext
def promote_admin(email):
    user = User.query.filter_by(email=email).first()
    if user:
        user.is_admin = True
        db.session.commit()
        click.echo(f"User with email {email} has been promoted to admin.")
    else:
        click.echo("User not found.")

@app.cli.command("remove-admin")
@click.argument("email")
@with_appcontext
def promote_admin(email):
    user = User.query.filter_by(email=email).first()
    if user:
        user.is_admin = False
        db.session.commit()
        click.echo(f"User with email {email} has been removed as admin.")
    else:
        click.echo("User not found.")





def allowed_file(file_storage):
    if not file_storage:
        return False  # No file provided
    # Check if the file extension is allowed
    filename = file_storage.filename
    is_allowed_extension = '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    # Ensure the file size is within the limit
    file_storage.seek(0, os.SEEK_END)
    file_size = file_storage.tell()
    is_allowed_size = file_size <= MAX_FILE_SIZE
    file_storage.seek(0)  # Reset file pointer

    # Check the file's content type (for images)
    file_content_type = imghdr.what(None, h=file_storage.read(MAX_FILE_SIZE))
    file_storage.seek(0)  # Reset file pointer
    is_allowed_content_type = 'image/' + file_content_type in ALLOWED_MIME_TYPES
    
    return is_allowed_extension and is_allowed_size and is_allowed_content_type


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    return "Rate limit exceeded", 429

@app.errorhandler(Exception)
def handle_exception(e):
    # pass the error to the template
    return render_template('error.html', error=e), 500

@app.route('/admin/dashboard/update_status/<int:antique_id>', methods=['POST'])
def update_status(antique_id):
    if 'user_id' not in session or not User.query.get(session['user_id']).is_admin:
        return redirect(url_for('login'))

    antique = Antique.query.get(antique_id)
    if antique:
        antique.status = "Accepted"
        db.session.commit()
        flash(f'Antique "{antique.name}" has been accepted.', 'success')
    else:
        flash('Antique not found.', 'warning')

    return redirect(url_for('admin_dashboard'))


# Start the Flask application
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables for our data models
    app.run(debug=True)
