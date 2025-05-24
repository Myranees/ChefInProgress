# import libraries
from flask import Flask, render_template, request, redirect, url_for, session, flash
import bcrypt
from pymongo import MongoClient
import os

# create Flask application
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')  # read from environment variable

#MONGODB CONNECTION
client = MongoClient('mongodb://localhost:27017/')
db = client['webtest']
user_col = db['webusers'] 

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        # get email and password from form
        email = request.form['email'].strip()
        password = request.form['password'].strip()

        # find user in database (need user_col from MongoDB setup)
        user_data = user_col.find_one({"email": email})

        if user_data:
            # check password hash
            if bcrypt.checkpw(password.encode('utf-8'), user_data['password']):
                # correct login: create session
                session['user_email'] = email
                flash("Logged in successfully!")
                return redirect(url_for('index')) 
            else:
                flash("Incorrect password. Please try again.")
        else:
            flash("Email not found. Please register.")

        # if login fails, redirect back to login page
        return redirect(url_for('login'))

    # if GET request, just render the login form
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    # if POST request, user starts registration
    if request.method == "POST":
        # collect form data
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        # basic validation
        if not username or not email or not password or not confirm_password:
            flash("Please fill in all fields.")
            return redirect(url_for('register'))

        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for('register'))

        # check if email already exists
        existing_user = user_col.find_one({"email": email})
        if existing_user:
            flash("An account with this email already exists.")
            return redirect(url_for('register'))

        # hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # save new user to database
        user_col.insert_one({
            "username": username,
            "email": email,
            "password": hashed_password
        })

        flash("Registration successful! Please log in.")
        return redirect(url_for('login'))

    # if GET request, show registration form
    return render_template('register.html')

@app.route('/myrecipes')
def myrecipes():
    return render_template('myrecipes.html')

@app.route('/recipedetails')
def recipe():
    return render_template('recipedetails.html')

@app.route('/addrecipe')
def addrecipe():
    return render_template('addrecipe.html')

@app.route('/test')
def test():
    return render_template('test.html')


if __name__ == '__main__':
    app.run(debug=True) 