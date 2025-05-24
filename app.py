# Import libraries
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

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/myrecipes')
def myrecipes():
    recipes = list(recipe_col.find())  # Fetch all recipes as a list of dicts from MongoDB
    return render_template('myrecipes.html', recipes=recipes)

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

@app.route('/test')
def test():
    return render_template('test.html')


if __name__ == '__main__':
    app.run(debug=True) 