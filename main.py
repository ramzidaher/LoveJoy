from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session
from datetime import datetime
from flask import flash, redirect, url_for
from datetime import timedelta
from sqlalchemy import create_engine, MetaData, Table
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from flask import render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
import os







# Initialize Flask App
app = Flask(__name__)


# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'  # Change to a random secret key

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.environ.get('GMAIL_USERNAME')  # Set as environment variable
app.config['MAIL_PASSWORD'] = os.environ.get('GMAIL_PASSWORD')  # Set as environment variable
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')






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
    is_admin = db.Column(db.Boolean, default=False, nullable=False)


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
    contact_method = db.Column(db.String(100), nullable=False)

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
        email = request.form['email']
        
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
        if profile_pic and allowed_file(profile_pic.filename):
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
        prefered_method = request.form['preferred_contact_method']

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
                user_id=current_user_id,  # Set the user_id field
                contact_method=prefered_method
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
            is_admin = current_user.is_admin
            # Get antiques associated with the current user
            current_user_antiques = Antique.query.filter_by(user_id=current_user_id).all()
            image_url = current_user.image_url

            if len(current_user_antiques) > 0:
                print("The list has items.")
            else:
                print("The list is empty.")
    return render_template('userdb.html', phonenumber=tel, emailaddr=email,username=name, current_user_antiques=current_user_antiques, image_url=image_url, is_admin=is_admin)



# SHOULD NOT BE ACCESSIBLE!!!!!!###
@app.route('/make_admin/<int:user_id>')
def make_admin(user_id):
    user = User.query.get(user_id)
    if user:
        user.is_admin = True
        db.session.commit()
        return f"User {user.name} is now an admin."
    else:
        return "User not found", 404

@app.route('/admin/')
def admin():
    if 'user_id' not in session or not User.query.get(session['user_id']).is_admin:
        return redirect(url_for('login'))

    users = User.query.all()
    
    # Filtering admin users and regular users
    admin_users = [user for user in users if user.is_admin]
    regular_users = [user for user in users if not user.is_admin]

    # Counting admin users and regular users
    total_users = len(users)
    total_admins = len(admin_users)
    total_regular_users = len(regular_users)
        
    return render_template('admin.html', total_users=total_users, total_admins=total_admins, total_regular_users=total_regular_users)



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



# Start the Flask application
if __name__ == '__main__':
    app.run(debug=True)