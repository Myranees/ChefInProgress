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
db = client["chef"] # use/create "webapp" database
recipe_col = db.recipe # use/create "recipe" collection
user_col = db['user'] # use/create "user" collection

# IMPORT AI_APIs.PY HERE
import AI_APIs # import the AI_APIs.py file

# new collections for AI APIs
googleai_text_col = db['googleai_text'] # use/create "googleai_text" collection

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
    recipes = list(recipe_col.find()) 
    return render_template('home.html', recipes=recipes)

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
            "password": hashed_password,
            "favorite": []
        })

        flash("Registration successful! Please log in.")
        return redirect(url_for('login'))

    # if GET request, show registration form
    return render_template('register.html')

@app.route('/savedrecipes')
def savedrecipes():
    if 'user_email' not in session:
        flash("Please login to view your saved recipes.")
        return redirect(url_for('login'))

    user = user_col.find_one({'email': session['user_email']})
    favorite_titles = user.get('favorites', [])

    # Fetch recipes that match any of the saved titles
    recipes = list(recipe_col.find({'title': {'$in': favorite_titles}}))

    return render_template('savedrecipes.html', recipes=recipes)

@app.route('/myrecipes')
def myrecipes():
    return render_template('myrecipes.html')

@app.route('/recipe/title/<recipe_title>')
def recipedetails(recipe_title):
    recipe = recipe_col.find_one({'title': recipe_title})
    if recipe:
        recipe['ingredients'] = recipe['ingredients'].split(';') if isinstance(recipe['ingredients'], str) else recipe['ingredients']
        recipe['instructions'] = recipe['instructions'].split(';') if isinstance(recipe['instructions'], str) else recipe['instructions']
        return render_template('recipedetails.html', data=recipe)
    abort(404)

@app.route('/add_to_favorites/<recipe_title>')
def add_to_favorites(recipe_title):
    if 'user_email' not in session:
        flash("Please login to save favorites.")
        return redirect(url_for('login'))

    user = user_col.find_one({'email': session['user_email']})
    recipe = recipe_col.find_one({'title': recipe_title})

    if user and recipe:
        if recipe_title not in user.get('favorites', []):
            user_col.update_one(
                {'email': session['user_email']},
                {'$push': {'favorites': recipe_title}}
            )
            flash(f"{recipe_title} added to your favorites!")
        else:
            flash(f"{recipe_title} is already in your favorites.")
    return redirect(url_for('savedrecipes'))

@app.route('/addrecipe')
def addrecipe():
    return render_template('addrecipe.html')

@app.route('/editrecipe')
def editrecipe():
    return render_template('editrecipe.html')

# 1. Google AI: Text generation route
@app.route('/google_text_generation', methods=['GET', 'POST'])
def google_text_generation():
    # handling a form is submitted via POST aka login data
    if request.method == "POST":
        # receive text data from POST form
        prompt_text = request.form['prompt_text'].strip()

        # get response text
        content = ""
        try:
            # call the AI_APIs.py function to generate text using Google Gemini AI
            content = AI_APIs.generate_text_gemini(prompt_text)
            # save into database
            # prepare the key values to be stored
            new_data = { "prompt_text": prompt_text, "response": content, "created_date": datetime.now()}
            googleai_text_col.insert_one(new_data)
            flash("The output/response has been successfully generated. Please check the result below.")
            
        except:
            flash("error calling the model")

        # get the data from database
        text_data = googleai_text_col.find({}).sort("_id", -1)
        text_data_list = list(text_data)
        
        return render_template("google_text_generation.html", output=content, prompt_text=prompt_text, data=text_data_list)
    
    # else (not POST aka GET) then
    # show the form and get the latest data from database
    text_data = googleai_text_col.find({}).sort("_id", -1)
    text_data_list = list(text_data)

    return render_template("google_text_generation.html", data=text_data_list)

# Get Google AI generated text detail
@app.route('/google_text_generation/<id>')
def google_text_generation_detail(id):
    data = ""
    try:
        _id_converted = ObjectId(id)
        search_filter = {"_id": _id_converted} # _id is key and _id_converted is the converted _id
        data = googleai_text_col.find_one(search_filter) # get one project data matched with _id
    except:
        print("ID is not found/invalid")
    
    return render_template("google_text_generation_detail.html", data=data)

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
