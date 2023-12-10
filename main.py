import os
import click
from datetime import datetime, timedelta
from PIL import Image

from flask import (
    Flask, flash, redirect, render_template, request, session, url_for
)
from flask.cli import with_appcontext
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemyc
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
from cryptography.fernet import Fernet
import random
import datetime
from markupsafe import Markup
from PIL import Image, ImageDraw, ImageFont
import random
import base64
import io
from flask import jsonify
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter








# Initialize Flask App
app = Flask(__name__)


# Database Configuration #
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/ramzidaher/Desktop/LoveJoy/instance/users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = '2e2ccdcef15c5a71fd7ba1ffa6f3a3d0'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.environ.get('GMAIL_USERNAME')  
app.config['MAIL_PASSWORD'] = os.environ.get('GMAIL_PASSWORD')  
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit





# File Upload Configuration
UPLOAD_FOLDER = 'static/uploads'  
UPLOAD_FOLDER_PROFILE = 'static/uploads/profilepics'
UPLOAD_FOLDER_EVALUATION = 'static/uploads/evaluation'
MAX_FAILED_ATTEMPTS = 7
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_FOLDER_PROFILE'] = UPLOAD_FOLDER_PROFILE
app.config['UPLOAD_FOLDER_EVALUATION'] = UPLOAD_FOLDER_EVALUATION


MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

ALLOWED_MIME_TYPES = {'image/png', 'image/jpeg', 'image/gif'}


"""INITIALIZATION """
# Initialize limiter
limiter = Limiter(
    key_func=get_remote_address, 
    app=app,
    default_limits=["200 per day", "50 per hour"]  # Default limits
)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Mail Initialize 
mail = Mail(app)

# Initialize SQLAlchemy
db = SQLAlchemy(app)



key = os.environ.get('FERNET_KEY')
cipher_suite = Fernet(key)


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
    security_question1 = db.Column(db.String(300), nullable=True)
    security_answer1 = db.Column(db.String(300), nullable=True)
    security_question2 = db.Column(db.String(300), nullable=True)
    security_answer2 = db.Column(db.String(300), nullable=True)
    security_question3 = db.Column(db.String(300), nullable=True)
    security_answer3 = db.Column(db.String(300), nullable=True)
    two_factor_code = db.Column(db.String(6), nullable=True)
    two_factor_expires = db.Column(db.DateTime, nullable=True)
    failed_login_attempts = db.Column(db.Integer, default=0)
    lockout_timestamp = db.Column(db.DateTime, nullable=True)
    verification_code = db.Column(db.String(100))  
    email_verified = db.Column(db.Boolean, default=False)  
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
    

#Main route page (landingpage)
@app.route('/')
def home():
    if 'user_id' not in session:
        return render_template('LandingPage.html')
    return redirect(url_for('homepage'))



# Token generation
def generate_verification_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-verification-salt')


# Token verification
def confirm_reset_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='email-verification-salt', max_age=expiration)
    except:
        return False
    return email


@app.route('/register', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email'].strip()

        # CAPTCHA validation
        user_input_captcha = request.form['captcha']
        if user_input_captcha != session.get('captcha_text', ''):
            flash('CAPTCHA Incorrect! Please try again.', 'error')
            return redirect(url_for('signup'))

        try:
            valid = validate_email(email)
            email = valid.email  
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

        security_question1 = request.form['security-question1']
        security_answer1 = encrypt_data(request.form['security-answer1'])
        security_question2 = request.form['security-question2']
        security_answer2 = encrypt_data(request.form['security-answer2'])
        security_question3 = request.form['security-question3']
        security_answer3 = encrypt_data(request.form['security-answer3'])

        profile_pic = request.files.get('profile-pic')
        if profile_pic and allowed_file(profile_pic):                   
            filename = secure_filename(profile_pic.filename)
            profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER_PROFILE'], filename))
            profile_pic_url = url_for('static', filename='uploads/profilepics/' + filename)
        else:
            profile_pic_url = None  # Or a default image path

        new_user = User(
            email=email,
            password=hashed_password,
            name=name,
            contact=contact,
            image_url=profile_pic_url,
            security_question1=security_question1,
            security_answer1=security_answer1,
            security_question2=security_question2,
            security_answer2=security_answer2,
            security_question3=security_question3,
            security_answer3=security_answer3,
        )
        token = generate_verification_token(new_user.email)
        new_user.verification_code = token  # Store the token
        db.session.add(new_user)
        db.session.commit()

        # Generate verification token

        # Create verification URL
        verify_url = url_for('email_verification', token=token, _external=True)

        # Send verification email
        msg = Message("Email Verification", sender=app.config['MAIL_DEFAULT_SENDER'], recipients=[new_user.email])
        msg.body = f"Please click the following link to verify your email: {verify_url}"
        mail.send(msg)

        flash('A verification email has been sent to your email address.', 'info')
        return redirect(url_for('login'))
    else:
        # Generate a new CAPTCHA for each GET request
        captcha_text = generate_captcha_text()
        session['captcha_text'] = captcha_text
        captcha_image = create_captcha_image(captcha_text)
        data = io.BytesIO()
        captcha_image.save(data, "PNG")
        encoded_image_data = base64.b64encode(data.getvalue()).decode('utf-8')
        return render_template('register.html', captcha_image_data=encoded_image_data)



@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  # Limit to 5 requests per minute
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember_me = request.form.get('remember_me')

        user = User.query.filter_by(email=username).first()
        if user:
            if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                flash('Account locked due to too many failed login attempts. Please try again later.', 'error')
                return render_template('login.html')

            if check_password_hash(user.password, password):
                if not user.email_verified:  # Check if email is verified
                    flash('Please verify your email before logging in.', 'error')
                    return render_template('login.html')

                # Reset the failed login attempts after successful login
                user.failed_login_attempts = 0
                # Generate 2FA code
                user.two_factor_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
                user.two_factor_expires = datetime.datetime.now() + datetime.timedelta(minutes=10)
                db.session.commit()

                # Send the code via email
                send_2fa_code_email(user.email, user.two_factor_code)

                # Store user ID in session to retrieve in 2FA verification route
                session['user_id_2fa'] = user.id

                if remember_me:
                    session.permanent = True
                    app.permanent_session_lifetime = timedelta(days=30)

                return redirect(url_for('two_factor_verify'))
            else:
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                    user.lockout_timestamp = datetime.utcnow()
                db.session.commit()
                flash('Invalid password. Please try again.', 'error')
        else:
            flash('Email not registered. Please check your email or register.', 'error')

    return render_template('login.html')




#Logs out the user and ends session
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
    
        if not allowed_file(antique_image):  
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
    name = email = tel = image_url= is_admin=None
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
    image_url = None  # Assign a default value to image_url

    if is_logged_in:
        current_user_id = session['user_id']
        current_user = User.query.filter_by(id=current_user_id).first()
        if current_user is not None:
            image_url = current_user.image_url

    all_antiques = Antique.query.all()  # Fetching all antiques

    return render_template('homepage.html', image_url=image_url, is_logged_in=is_logged_in, all_antiques=all_antiques)






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
            token = generate_verification_token(user.email)
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
    email = confirm_reset_token(token)
    if not email:
        # Token is invalid or expired
        flash('Token is invalid or expired!', 'warning')
        return redirect(url_for('reset_request'))

    if request.method == "POST":
        user = User.query.filter_by(email=email).first()
        if user:
            user.password = generate_password_hash(request.form['password'])
            db.session.commit()
            flash('Your password has been updated!', 'success')
            return redirect(url_for('login'))
        else:
            flash('User not found.', 'error')
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


# ERROR PAGES #
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


@app.route('/admin/antiques')
def manage_antiques():
    if 'user_id' not in session or not User.query.get(session['user_id']).is_admin:
        return redirect(url_for('login'))

    antiques = Antique.query.all()  # Fetching all antiques from the database

    return render_template('manage_antiques.html', antiques=antiques)


@app.route('/admin/antiques/edit/<int:antique_id>', methods=['GET', 'POST'])
def edit_antique(antique_id):
    antique = Antique.query.get_or_404(antique_id)
    
    if request.method == 'POST':
        # Update antique details based on form input
        antique.name = request.form['name']
        antique.description = request.form['description']
        antique.age = request.form['age']

        db.session.commit()
        flash('Antique updated successfully.', 'success')
        return redirect(url_for('manage_antiques'))
    
    return render_template('edit_antique.html', antique=antique)

@app.route('/admin/antiques/delete/<int:antique_id>', methods=['POST'])
def delete_antique(antique_id):
    antique = Antique.query.get_or_404(antique_id)

    db.session.delete(antique)
    db.session.commit()
    flash('Antique deleted successfully.', 'success')
    
    return redirect(url_for('manage_antiques'))

# Data Encryption #
def encrypt_data(data):
    return cipher_suite.encrypt(data.encode()).decode()

def generate_2fa_code():
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

def send_2fa_code_email(email, code):
    msg = Message("Your 2FA Code", sender=app.config['MAIL_DEFAULT_SENDER'], recipients=[email])
    msg.body = f"Your two-factor authentication code is: {code}"
    mail.send(msg)


@app.route('/verify_2fa', methods=['GET', 'POST'])
def two_factor_verify():
    user_id = session.get('user_id_2fa')
    if not user_id:
        return redirect(url_for('login'))

    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('login'))

    if request.method == 'POST':
        code = request.form.get('code')
        if user.two_factor_code == code and datetime.datetime.now() < user.two_factor_expires:
            # Log the user in
            session['user_id'] = user.id
            session['username'] = user.name
            user.two_factor_code = None  # Clear the 2FA code
            db.session.commit()
            return redirect(url_for('homepage'))
        else:
            flash('Invalid or expired 2FA code', 'error')

    return render_template('verify_2fa.html')

@app.route('/reset_lockout/<int:user_id>', methods=['GET'])
def reset_lockout(user_id):
    if 'user_id' not in session or not User.query.get(session['user_id']).is_admin:
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))

    user = User.query.get(user_id)
    if user:
        user.failed_login_attempts = 0
        user.lockout_timestamp = None
        db.session.commit()
        flash(f"Lockout reset for user {user.email}.", "success")
    else:
        flash("User not found.", "error")

    return redirect(url_for('admin_dashboard'))


@app.route('/verify_email/<verification_code>', methods=['GET'])
def verify_email(verification_code):
    # Find the user by verification code
    user = User.query.filter_by(verification_code=verification_code).first()
    
    if user:
        # Mark the user's email as verified
        user.email_verified = True
        user.verification_code = None  # Clear the verification code
        db.session.commit()
        
        flash('Email verified successfully. You can now log in.', 'success')
    else:
        flash('Invalid verification code. Please try again.', 'error')

    return redirect(url_for('login'))

def generate_captcha_text():
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))



def create_captcha_image(captcha_text):
    # Create an image with white background
    image = Image.new('RGB', (150, 60), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)

    font_size = 30
    for i, char in enumerate(captcha_text):
        x = 10 + i * 25  
        y = random.randint(0, 15)  
        font = ImageFont.truetype('/home/ramzidaher/Desktop/LoveJoy/static/arial.ttf', font_size)
        color = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200)) 
        draw.text((x, y), char, font=font, fill=color)

    width, height = image.size
    for _ in range(random.randint(5, 10)):  
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        draw.line(((x1, y1), (x2, y2)), fill='black', width=1)

    for _ in range(random.randint(100, 200)):  
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.point((x, y), fill='black')

    return image


@app.route('/regenerate_captcha')
def regenerate_captcha():
    captcha_text = generate_captcha_text()
    session['captcha_text'] = captcha_text
    captcha_image = create_captcha_image(captcha_text)
    data = io.BytesIO()
    captcha_image.save(data, "PNG")
    encoded_image_data = base64.b64encode(data.getvalue()).decode('utf-8')
    return jsonify({'captcha_image_data': encoded_image_data})

def generate_verification_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-verification-salt')




@app.route('/verify_email/<token>', methods=['GET'])
def email_verification(token):
    try:
        email = URLSafeTimedSerializer(app.config['SECRET_KEY']).loads(token, salt='email-verification-salt', max_age=3600)
    except:
        return 'The verification link is invalid or has expired', 400

    user = User.query.filter_by(email=email).first_or_404()
    user.email_verified = True
    db.session.commit()
    return 'Email verified successfully!'

# Initializ DataBase #
@app.cli.command("init-db")
@with_appcontext
def init_db_command():
    """Clear existing data and create new tables."""
    db.create_all()
    click.echo("Initialized the database.")



# Start the Flask application
if __name__ == '__main__':
    app.run(debug=False)
