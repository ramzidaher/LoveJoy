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
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
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
    
# Product Model (may need tobe removed later on)
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(300), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    # category = db.Column(db.String(100), nullable=True)
    price = db.Column(db.Float, nullable=True)
    # stock_quantity = db.Column(db.Integer, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
        # user = db.relationship('User', backref=db.backref('products', lazy=True))


# # Antique Evaluation
class Antique(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    age = db.Column(db.Integer, nullable=True)  # Assuming age is in years
    origin = db.Column(db.String(100), nullable=True)  # Place of origin
    condition = db.Column(db.String(100), nullable=True)  # Condition of the item
    # price = db.Column(db.Float, nullable=True)
    # acquired_date = db.Column(db.DateTime, nullable=True)
    image_url = db.Column(db.String(300), nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    owner = db.relationship('User', backref=db.backref('antiques', lazy=True))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    owner = db.relationship('User', foreign_keys=[user_id], backref=db.backref('antiques', lazy=True))


    def __repr__(self):
        return f'<Antique {self.name}>'
    

@app.before_first_request
def create_tables():
    db.create_all()



# Create the database tables before the first request# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/register', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        plain_text_password = request.form['password']
        hashed_password = generate_password_hash(plain_text_password)
        name = request.form['name']
        contact = request.form['contact']
        new_user = User(email=email, password=hashed_password, name=name, contact=contact)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))  
    return render_template('register.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember_me = request.form.get('remember_me')  # Assuming the checkbox name is 'remember_me'
        
        user = User.query.filter_by(email=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.name

            # Set session to be permanent if 'Remember Me' is checked
            if remember_me:
                session.permanent = True
                app.permanent_session_lifetime = timedelta(days=30)  # Example: 30 days

            return redirect(url_for('profiledb'))
        else:
            return render_template('login.html', error="Invalid username or password")

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


#Main route page (landingpage)
@app.route('/')
def home():
    return render_template('LandingPage.html')


@app.route('/products')
def show_products():
    all_products = Product.query.all()

    current_user_products = []
    if 'user_id' in session:
        current_user_id = session['user_id']
        current_user_products = Product.query.filter_by(user_id=current_user_id).all()

    return render_template('products.html', all_products=all_products, current_user_products=current_user_products)

@app.route('/profile', methods=['GET', 'POST'])
def profiledb():
    all_antiques = Antique.query.all()
    name = None 

    current_user_antique = []
    if 'user_id' in session:
        current_user_id = session['user_id']
        current_user = User.query.filter_by(id=current_user_id).first()
        if current_user:
            name = current_user.name  
            email = current_user.email
            tel = current_user.contact
            current_user_antique = Antique.query.filter_by(user_id=current_user_id).all()
        return render_template('userdb.html',current_user_antique=current_user_antique, )
    else :
        return render_template('LandingPage.html')

    # if request.method == 'POST':    
    #     product_name = request.form['product_name']
    #     product_description = request.form['product_description']
    #     file = request.files['product_image']

    #     if file and allowed_file(file.filename):
    #         filename = secure_filename(file.filename)
    #         file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    #         file.save(file_path)

    #         new_product = Product(
    #             name=product_name,
    #             description=product_description,
    #             image_url=filename,
    #             user_id=session['user_id']
    #         )

    #         db.session.add(new_product)
    #         db.session.commit() 

    #         return redirect(url_for('profiledb'))
    # return render_template('userdb.html',phonenumber=tel,emailaddr=email, username=name, current_user_products=current_user_products)



@app.route('/evaluation',methods=['GET', 'POST'])
def evauluateAntique():           
    if 'user_id' not in session:
        return render_template('login.html')
    
    current_user_id = session['user_id']
    current_user = User.query.filter_by(id=current_user_id).first()
    if not current_user:
        # Handle case where current_user is not found
        flash("User not found.", "error")
        return redirect(url_for('login'))  # Assuming 'login' is your login page

    if request.method == 'POST':
        print("IN POST")
        anti_name = request.form['antique_name']
        anti_description = request.form['antique_description']
        anti_age = request.form['antique_est_age']
        # Handle file upload
        antique_image = request.files['antique_image']
        if antique_image.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)

        if antique_image and allowed_file(antique_image.filename):  # Implement allowed_file function to check file types
            filename = secure_filename(antique_image.filename)
            antique_image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # Create and save the Antique object
            new_antique = Antique(
                name=anti_name,
                description=anti_description,
                age=anti_age,
                # other fields...
                owner_id=current_user_id,
                image_url=filename  # or a path to the file
            )
            db.session.add(new_antique)
            db.session.commit()
            flash("Antique successfully uploaded for evaluation!", "success")
            return render_template('antiquebeingevaluated.html')
        else:
            flash('Invalid file type', 'error')

    return render_template('/evaluation.html')





# Start the Flask application
if __name__ == '__main__':
    app.run(debug=True)