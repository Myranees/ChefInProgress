# import libraries
from flask import Flask, render_template, url_for, redirect, request, session, flash, abort, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId #import this to convert ObjectID from string to it's datatype in MongoDB
import functools
import bcrypt # to encrypt password
import os
from os.path import join, dirname, realpath
from werkzeug.utils import secure_filename # for secure name
from datetime import datetime #datetime
import re
from markupsafe import Markup

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

# Create directory if it doesn't exist
os.makedirs(FULL_UPLOAD_FOLDER, exist_ok=True)

# for session
app.secret_key = 'fad62b7c1a6a9e67dbb66c3571a23ff2425650965f80047ea2fadce543b088cf'

#accessing filename
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#convert hour in time to minutes 
def convert_to_minutes(time_str):
    try:
        if not time_str:
            return 0
        time_str = time_str.lower()
        num = int(time_str.split()[0])
        if 'hour' in time_str:
            return num * 60
        elif 'min' in time_str:
            return num
        else:
            return 0
    except:
        return 0

@app.route('/')
def index():
    recipes = list(recipe_col.find()) 
    cuisine = request.args.get('cuisine')
    query = request.args.get('query')
    user = user_col.find_one({'email': session['user_email']})
    favorite_titles = user.get('favorites', [])
    filtered_recipes = []

    if cuisine or query:
        filter_query = {}

        if cuisine:
            filter_query["category"] = {"$regex": f"^{cuisine}$", "$options": "i"}

        if query:
            filter_query["title"] = {"$regex": query, "$options": "i"}

        filtered_recipes = list(recipe_col.find(filter_query))

        for recipe in filtered_recipes:
            prep_time = convert_to_minutes(recipe.get("prep_time", "0"))
            cook_time = convert_to_minutes(recipe.get("cook_time", "0"))
            recipe['total_time'] = prep_time + cook_time

    return render_template('home.html',
                       recipes=recipes,
                       filtered_recipes=filtered_recipes,
                       selected_cuisine=cuisine,
                       search_query=query,
                       user_favorites=favorite_titles,
                       user=user)

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
            "created_recipe": [],
            "profile_pic": "default_profile.png"
        })

        flash("Registration successful! Please log in.")
        return redirect(url_for('login'))

    # if GET request, show registration form
    return render_template('register.html')

@app.route('/searchresults')
def searchresults():
    query = request.args.get('query', '')
    if query:
        results = recipe_col.find({
            "ingredients": {"$regex": query, "$options": "i"}
        })
        return render_template('searchresults.html', query=query, recipes=results)
    else:
        return render_template('searchresults.html', query=query, results=[])

@app.route('/savedrecipes')
def savedrecipes():
    if 'user_email' not in session:
        flash("Please login to view your saved recipes.")
        return redirect(url_for('login'))

    user = user_col.find_one({'email': session['user_email']})
    favorite_titles = user.get('favorites', [])

    # Fetch all recipes matching favorites
    all_recipes = list(recipe_col.find({'title': {'$in': favorite_titles}}))

    # Pagination setup
    per_page = 12
    page = request.args.get('page', 1, type=int)  # get page number from query params, default 1
    total = len(all_recipes)
    start = (page - 1) * per_page
    end = start + per_page

    # Slice the list for current page
    recipes = all_recipes[start:end]

    total_pages = (total + per_page - 1) // per_page  # ceil division to get total pages

    return render_template('savedrecipes.html',
                           recipes=recipes,
                           user_favorites=favorite_titles,
                           page=page,
                           total_pages=total_pages,
                           total=total,
                           per_page=per_page)
@app.route('/myrecipes')
def myrecipes():
    if 'user_email' not in session:
        flash("Please login to view your saved recipes.")
        return redirect(url_for('login'))

    # Fetch uploaded recipes (recipes where prepared_by matches current user)
    uploaded_recipes = list(recipe_col.find({'prepared_by': session['username']}))
    
    return render_template('myrecipes.html', uploaded_recipes=uploaded_recipes)

@app.route('/recipe/<recipe_id>')
def recipedetails(recipe_id):
    try:
        recipe = recipe_col.find_one({'_id': ObjectId(recipe_id)})
        if recipe:
            recipe['ingredients'] = recipe['ingredients'].split(';') if isinstance(recipe['ingredients'], str) else recipe['ingredients']
            recipe['instructions'] = recipe['instructions'].split(';') if isinstance(recipe['instructions'], str) else recipe['instructions']
            return render_template('recipedetails.html', data=recipe)
    except:
        pass
    abort(404)


from bson.objectid import ObjectId
from flask import abort

@app.route('/toggle_favorite/<recipe_id>')
def toggle_favorite(recipe_id):
    if 'user_email' not in session:
        flash("Please login to manage favorites.")
        return redirect(url_for('login'))

    try:
        obj_id = ObjectId(recipe_id)
    except:
        abort(400, description="Invalid recipe ID format.")

    user = user_col.find_one({'email': session['user_email']})
    recipe = recipe_col.find_one({'_id': obj_id})

    if user and recipe:
        favorites = user.get('favorites', [])
        if recipe_id in favorites:
            user_col.update_one(
                {'email': session['user_email']},
                {'$pull': {'favorites': recipe_id}}
            )
            flash(f"{recipe['title']} removed from your favorites.")
        else:
            user_col.update_one(
                {'email': session['user_email']},
                {'$push': {'favorites': recipe_id}}
            )
            flash(f"{recipe['title']} added to your favorites!")
    
    return redirect(request.referrer or url_for('home'))

@app.route('/addrecipe', methods=['GET', 'POST'])
def addrecipe():
    if request.method == 'POST':
        try:
            # Extract form fields
            title = request.form.get('title', '').strip()
            category = request.form.get('cuisine', '').strip()
            description = request.form.get('description', '').strip()
            prep_time = request.form.get('prep_time', '').strip()
            cook_time = request.form.get('cook_time', '').strip()
            servings = request.form.get('servings', '').strip()
            ingredients = [s.strip() for s in request.form.getlist('ingredients[]') if s.strip()]
            step_texts = [s.strip() for s in request.form.getlist('steps[]') if s.strip()]
            step_images = request.files.getlist('steps_images[]')

            # Basic validation
            if not title or not category or not description or not ingredients or not step_texts:
                flash("Please fill in all required fields.")
                return redirect(url_for('addrecipe'))

            # Recipe image
            image_file = request.files.get('image')
            image_filename = None
            if image_file and allowed_file(image_file.filename):
                filename = secure_filename(image_file.filename)
                unique_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
                image_file.save(image_path)
                image_filename = f"uploads/{unique_name}"

            # Step instructions with images
            step_data = []
            for i, text in enumerate(step_texts):
                img_path = None
                if i < len(step_images):
                    img_file = step_images[i]
                    if img_file and allowed_file(img_file.filename):
                        step_filename = secure_filename(img_file.filename)
                        step_unique = f"step_{i}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{step_filename}"
                        img_file.save(os.path.join(app.config['UPLOAD_FOLDER'], step_unique))
                        img_path = f"uploads/{step_unique}"
                step_data.append({"text": text, "image": img_path})

            # Recipe document
            recipe = {
                'title': title,
                'category': category,
                'prepared_by': session.get('username', 'Anonymous'),
                'prep_time': prep_time,
                'cook_time': cook_time,
                'servings': servings,
                'image': image_filename,
                'description': description,
                'ingredients': ingredients,
                'instructions': step_data
            }
            
            # Insert recipe and get inserted ID
            result = recipe_col.insert_one(recipe)
            recipe_id = result.inserted_id

            # Update user's created_recipe list
            username = session.get('username')
            if username:
                user_col.update_one(
                    {"username": username},
                    {"$push": {"created_recipe": recipe_id}}
                )

            flash("Recipe added successfully!")
            return redirect(url_for('myrecipes'))

        except Exception as e:
            flash(f"An error occurred while saving: {str(e)}")
            return redirect(url_for('addrecipe'))

    return render_template('addrecipe.html')

from bson.objectid import ObjectId

@app.route('/editrecipe/<recipe_id>', methods=['GET', 'POST'])
def editrecipe(recipe_id):
    if 'username' not in session:
        flash("Please log in to edit your recipe.")
        return redirect(url_for('login'))

    try:
        obj_id = ObjectId(recipe_id)
    except:
        flash("Invalid recipe ID format.")
        return redirect(url_for('myrecipes'))

    # Find the recipe using ObjectId and author
    recipe = recipe_col.find_one({'_id': obj_id, 'prepared_by': session['username']})
    if not recipe:
        flash("Recipe not found or you don't have permission to edit it.")
        return redirect(url_for('myrecipes'))

    if request.method == 'POST':
        try:
            title = request.form.get('title', '').strip()
            category = request.form.get('cuisine', '').strip()
            description = request.form.get('description', '').strip()
            prep_time = request.form.get('prep_time', '').strip()
            cook_time = request.form.get('cook_time', '').strip()
            servings = request.form.get('servings', '').strip()
            ingredients = [s.strip() for s in request.form.getlist('ingredients[]') if s.strip()]
            step_texts = [s.strip() for s in request.form.getlist('steps[]') if s.strip()]
            step_images = request.files.getlist('steps_images[]')
            delete_flags = request.form.getlist('delete_step_images[]')

            if not title or not category or not description or not ingredients or not step_texts:
                flash("Please fill in all required fields.")
                return redirect(url_for('editrecipe', recipe_id=recipe_id))

            image_file = request.files.get('image')
            image_filename = recipe.get('image')
            if image_file and allowed_file(image_file.filename):
                if image_filename and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], image_filename.replace('uploads/', ''))):
                    try:
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image_filename.replace('uploads/', '')))
                    except:
                        pass
                filename = secure_filename(image_file.filename)
                unique_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
                image_file.save(image_path)
                image_filename = f"uploads/{unique_name}"

            step_data = []
            existing_steps = recipe.get('instructions', [])

            for i, text in enumerate(step_texts):
                img_path = None
                if i < len(existing_steps):
                    img_path = existing_steps[i].get('image')

                delete_flag = delete_flags[i] == '1' if i < len(delete_flags) else False
                if delete_flag and img_path:
                    try:
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], img_path.replace('uploads/', '')))
                    except:
                        pass
                    img_path = None

                if i < len(step_images):
                    img_file = step_images[i]
                    if img_file and allowed_file(img_file.filename):
                        if img_path:
                            try:
                                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], img_path.replace('uploads/', '')))
                            except:
                                pass
                        step_filename = secure_filename(img_file.filename)
                        step_unique = f"step_{i}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{step_filename}"
                        img_file.save(os.path.join(app.config['UPLOAD_FOLDER'], step_unique))
                        img_path = f"uploads/{step_unique}"

                step_data.append({"text": text, "image": img_path})

            updated_recipe = {
                'title': title,
                'category': category,
                'prepared_by': session.get('username', 'Anonymous'),
                'prep_time': prep_time,
                'cook_time': cook_time,
                'servings': servings,
                'image': image_filename,
                'description': description,
                'ingredients': ingredients,
                'instructions': step_data
            }

            recipe_col.update_one({'_id': recipe['_id']}, {'$set': updated_recipe})

            flash("Recipe updated successfully!")
            return redirect(url_for('recipedetails', recipe_id=recipe_id))

        except Exception as e:
            flash(f"An error occurred while updating: {str(e)}")
            return redirect(url_for('editrecipe', recipe_id=recipe_id))

    return render_template('editrecipe.html', recipe=recipe)

@app.route('/deleterecipe/<recipe_id>')
def deleterecipe(recipe_id):
    try:
        recipe = recipe_col.find_one({"_id": ObjectId(recipe_id)})
        if recipe:
            recipe_col.delete_one({"_id": ObjectId(recipe_id)})
            flash('Recipe deleted successfully!', 'success')
        else:
            flash('Recipe not found.', 'danger')
    except Exception as e:
        flash(f"Error deleting recipe: {e}", 'danger')

    return redirect(url_for('myrecipes'))

@app.template_filter('format_output')
def markdown_bold(text):
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = text.replace('\n', '<br>')
    return Markup(text)  # Mark as safe HTML

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_email' not in session:
        flash("Please log in to access your profile.")
        return redirect(url_for('login'))

    user = user_col.find_one({'email': session['user_email']})
    # Get array of recipe IDs created by this user
    created_recipes = list(recipe_col.find(
        {'prepared_by': user['username']},
        {'_id': 1}  # Only return the IDs
    ))
    
    # Convert ObjectIds to strings for easier handling in template
    user['created_recipe'] = [str(recipe['_id']) for recipe in created_recipes]
    
    if request.method == 'POST':
        name = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        new_password = request.form.get('password', '').strip()
        old_password = request.form.get('old_password', '').strip()
        profile_pic = request.files.get('profile_pic')

        # Check if username already exists (excluding current user)
        if name and name != user['username']:
            existing_user = user_col.find_one({
                'username': name,
                '_id': {'$ne': user['_id']}  # Exclude current user from check
            })
            if existing_user:
                flash("Username already taken. Please choose another.", "danger")
                return redirect(url_for('profile'))
            
        update_fields = {
            'username': name,
            'email': email
        }

        # Check and update password only if provided
        if new_password:
            if not old_password:
                flash("Please enter your current password to set a new one.", "danger")
                return redirect(url_for('profile'))

            # Verify old password
            if not bcrypt.checkpw(old_password.encode('utf-8'), user['password']):
                flash("Incorrect current password.", "danger")
                return redirect(url_for('profile'))

            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            update_fields['password'] = hashed_password

        # Handle profile picture upload
        if profile_pic and allowed_file(profile_pic.filename):
            filename = secure_filename(profile_pic.filename)
            unique_name = f"profile_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
            profile_pic.save(filepath)
            update_fields['profile_pic'] = unique_name
         
         # If username is being changed, update recipes
        old_username = user['username']
        if name and name != old_username:
            # Update recipes where the user is the author
            recipe_col.update_many({'prepared_by': old_username}, {'$set': {'prepared_by': name}})
    
        # Update user in DB
        user_col.update_one({'email': session['user_email']}, {'$set': update_fields})

        # Update session and reload user
        session['user_email'] = email
        session['username'] = name
        flash("Profile updated successfully!")
        return redirect(url_for('profile'))

    return render_template('profile.html', user=user)

@app.context_processor
def inject_user():
    user = None
    if 'user_email' in session:
        user = user_col.find_one({'email': session['user_email']})
    return dict(user=user)
def inject_recipe_col():
    return dict(recipe_col=recipe_col)

@app.route('/AIrecipe', methods=['GET', 'POST'])
def AIrecipe():
    # Check if user is logged in
    if 'user_email' not in session:
        flash("Please log in to access your profile.")
        return redirect(url_for('login'))
    
    current_user_email = session['user_email']
    prompt_text = ""
    output = ""
    selected_id = request.args.get('selected_id')
    history = list(googleai_text_col.find({"user_id": current_user_email}).sort("_id", -1))
    
    if request.method == "POST":
        # receive text data from  form
        prompt_text = request.form['prompt_text'].strip()

        try:
            
            output = AI_APIs.generate_text_gemini(prompt_text)   # call the AI_APIs.py function to generate text using Google Gemini AI

            new_data = {
                "prompt_text": prompt_text, 
                "response": output, 
                "created_date": datetime.now(), 
                "user_id": current_user_email
                }
            
            googleai_text_col.insert_one(new_data)
            flash("The output/response has been successfully generated. Please check the result below.")
            history.insert(0, new_data)
            
        except:
            flash("error calling the model")
            
        return render_template("AIrecipe.html", history=history, output=output, prompt_text=prompt_text, selected_id=None)
       
    # Handle view detail of a specific prompt
    if selected_id:
        try:
            _id_converted = ObjectId(selected_id)
            selected = googleai_text_col.find_one({"_id": _id_converted, "user_id": current_user_email }) # get one project data matched with _id
            print("ID SELECTED")
            if selected:
                prompt_text = selected.get("prompt_text", "")
                output = selected.get("response", "")
        except:
            print("ID is not found/invalid")
            
        
    return render_template(
        "AIrecipe.html",
        history=history,
        output=output,
        prompt_text=prompt_text,
        selected_id=selected_id)
                        

@app.route('/logout')
def logout():
    session.clear()  # remove all session data
    flash("You’ve been logged out successfully.")
    return redirect(url_for('login'))

@app.route('/test')
def test():
    return render_template('test.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
