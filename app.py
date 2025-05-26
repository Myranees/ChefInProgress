# import libraries
from flask import Flask, render_template, url_for, redirect, request, session, flash, abort
from pymongo import MongoClient
from bson.objectid import ObjectId #import this to convert ObjectID from string to it's datatype in MongoDB
import functools
import bcrypt # to encrypt password
import os
from os.path import join, dirname, realpath
from werkzeug.utils import secure_filename # for secure name
from datetime import datetime #datetime

client = MongoClient("mongodb://localhost:27017/") # connect on the "localhost" host and port 27017
db = client["webtest"] # use/create "webapp" database
recipe_col = db.recipe # use/create "recipe" collection
user_col = db['webusers'] # use/create "user" collection

# create Flask application
app = Flask(__name__)

# settings for uploading files feature
PATH_UPLOAD = 'static/uploads'
FULL_UPLOAD_FOLDER = join(dirname(realpath(__file__)), PATH_UPLOAD) #path for uploaded files
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
# set the config for upload folder
app.config['UPLOAD_FOLDER'] = FULL_UPLOAD_FOLDER

# for session
app.secret_key = 'fad62b7c1a6a9e67dbb66c3571a23ff2425650965f80047ea2fadce543b088cf'

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
                session['username'] = user_data['username']
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
    username = session.get('username')
    if not username:
        flash("Please log in to view your recipes.")
        return redirect(url_for('login'))

    my_recipes = list(recipe_col.find({'prepared_by': username}))

    saved_recipe_ids = session.get('saved_recipe_ids', [])
    saved_recipes = list(recipe_col.find({'_id': {'$in': [ObjectId(id) for id in saved_recipe_ids]}}))

    return render_template('myrecipes.html', 
                           saved_recipes=saved_recipes, 
                           my_recipes=my_recipes)

@app.route('/recipe/title/<recipe_title>')
def recipedetails(recipe_title):
    recipe = recipe_col.find_one({'title': recipe_title})
    if recipe:
        recipe['ingredients'] = recipe['ingredients'].split(';') if isinstance(recipe['ingredients'], str) else recipe['ingredients']
        recipe['instructions'] = recipe['instructions'].split(';') if isinstance(recipe['instructions'], str) else recipe['instructions']
        return render_template('recipedetails.html', data=recipe)
    abort(404)

@app.route('/addrecipe')
def addrecipe():
    return render_template('addrecipe.html')

@app.route('/logout')
def logout():
    session.clear()  # remove all session data
    flash("You’ve been logged out successfully.")
    return redirect(url_for('login'))

@app.route('/test')
def test():
    return render_template('test.html')

if __name__ == '__main__':
    app.run(debug=True) 
