# Import libraries
from flask import Flask, render_template, url_for, redirect, request, session, flash

# create Flask application
app = Flask(__name__)

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