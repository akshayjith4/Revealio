from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_cors import CORS
import sqlite3
import os
import json
import bcrypt
import base64
from werkzeug.utils import secure_filename
from ocr import extract_text  # OCR Function
from ml_lookup import check_allergen_risk  # ML Model for Risk Assessment
from alternative import get_alternative  # Alternative Food Recommender

# Initialize Flask App
app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'your_secret_key'
CORS(app)

# Database & Upload Configuration
DATABASE = 'users.db'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ✅ Database Connection
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Access rows by column name
    return conn

# ✅ Initialize Database
def init_db():
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                allergies TEXT,
                health_conditions TEXT,
                diet TEXT
            )
        ''')
        conn.commit()

# ✅ Home Page
@app.route('/')
def home():
    return render_template('index.html')

# ✅ Register Page
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        allergies = request.form.getlist("allergies")
        health_conditions = request.form.getlist("health_conditions")
        diet = request.form.get("diet")

        # Remove "None" from lists
        allergies = ", ".join([a for a in allergies if a != "None"]) or "None"
        health_conditions = ", ".join([h for h in health_conditions if h != "None"]) or "None"

        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        try:
            with get_db_connection() as conn:
                conn.execute(
                    "INSERT INTO users (username, email, password, allergies, health_conditions, diet) VALUES (?, ?, ?, ?, ?, ?)",
                    (username, email, hashed_password, allergies, health_conditions, diet),
                )
                conn.commit()
                flash("✅ Registration successful! You can now log in.", "success")
                return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("⚠️ Username or email already exists. Try a different one.", "error")

    return render_template("register.html")

# ✅ Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        with get_db_connection() as conn:
            user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            session['user'] = user['username']
            flash(f"✅ Welcome back, {user['username']}!", "success")
            return redirect(url_for('upload'))
        else:
            flash("❌ Invalid Username or Password!", "danger")

    return render_template('login.html')

# ✅ Check Allowed File Extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ✅ Upload & OCR Processing + ML Integration
@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "user" not in session:
        flash("⚠️ Please log in first!", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        file = request.files.get("image")
        captured_image = request.form.get("captured-image")

        if file and allowed_file(file.filename):
            # ✅ Handle Browsed Image
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

        elif captured_image:
            # ✅ Handle Captured Image (Convert from Base64)
            filename = "captured_image.png"
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            image_data = base64.b64decode(captured_image.split(",")[1])  # Remove "data:image/png;base64,"
            with open(filepath, "wb") as img_file:
                img_file.write(image_data)

        else:
            flash("⚠️ No file selected!", "danger")
            return redirect(request.url)

        try:
            extracted_text, processed_path = extract_text(filepath)
            username = session.get("user", "Guest")

            ml_result = check_allergen_risk(username, extracted_text)

            # ✅ Store results in session
            session["ml_result"] = json.dumps(ml_result)
            session["extracted_text"] = extracted_text

            flash("✅ Analysis completed successfully!", "success")
            return redirect(url_for("results"))

        except Exception as e:
            flash(f"❌ Error processing image: {str(e)}", "danger")
            return redirect(url_for("upload"))

    return render_template("upload.html")


# ✅ Result Page
@app.route('/results')
def results():
    username = session.get('user')
    extracted_text = session.get('extracted_text')
    ml_result = session.get('ml_result')

    # Convert JSON string to dict
    if ml_result:
        try:
            ml_result = json.loads(ml_result)
        except json.JSONDecodeError:
            flash("⚠️ Error loading analysis. Please try again.", "warning")
            return redirect(url_for('upload'))
    else:
        flash("⚠️ No analysis found. Please upload an image.", "warning")
        return redirect(url_for('upload'))

    analysis_results = ml_result.get("analysis_results", [])
    unsafe_ingredients = ml_result.get("unsafe_ingredients", [])

    # ✅ Store `unsafe_ingredients` in session properly
    session['unsafe_ingredients'] = json.dumps(unsafe_ingredients)

    return render_template('result.html', 
                        analysis_results=analysis_results, 
                        extracted_text=extracted_text, 
                        username=username, 
                        unsafe_ingredients=unsafe_ingredients)


# ✅ Alternative Food Recommendation
@app.route("/recommendation")
def recommendation():
    username = session.get("user", "Guest")

    # ✅ Retrieve and normalize unsafe ingredients
    unsafe_ingredients = session.get("unsafe_ingredients", "[]")  # Default to empty list
    unsafe_ingredients = json.loads(unsafe_ingredients)  # Convert back to list
    unsafe_ingredients = [ing.lower().strip() for ing in unsafe_ingredients]  # Ensure lowercase

    # ✅ Fetch alternatives
    recommendations = get_alternative(unsafe_ingredients)

    # ✅ Print alternatives for debugging
    print("\n🥗 **Alternative Recommendations**")
    for ingredient, alternative in recommendations.items():
        print(f"✅ {ingredient.capitalize()} → {alternative}")

    return render_template("recommendation.html", 
                        username=username, 
                        unsafe_ingredients=unsafe_ingredients, 
                        recommendations=recommendations)


# ✅ Logout
@app.route('/logout')
def logout():
    session.clear()
    flash("👋 You have been logged out.", "info")
    return redirect(url_for('login'))

# ✅ Run the App
if __name__ == '__main__':
    init_db()  # Ensure database exists
    app.run(debug=True)
