import os
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from helpers import login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["UPLOAD_FOLDER"] = "/pics"
app.config["MAX_CONTENT_PATH"] = 5000000

Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///project.db")

@app.route("/")
def index():

    if request.method == "POST":

        status = request.form.get("status")
        location = request.form.get("location")
        breed = request.form.get("breed")
        color = request.form.get("color")

        if not status:
            errorMsg = "Must provide status!"
            return render_template("index.html", errorMsg=errorMsg)

        if not location:
            errorMsg = "Must provide location!"
            return render_template("index.html", errorMsg=errorMsg)

        if not breed:
            errorMsg = "Must provide breed!"
            return render_template("index.html", errorMsg=errorMsg)

        if not color:
            errorMsg = "Must provide color!"
            return render_template("index.html", errorMsg=errorMsg)

        rows = db.execute("SELECT name, email, dog_name, status, located, picture, breed, color FROM dogs JOIN users ON users.id = dogs.id_user")

        return render_template("index.html", rows=rows)

    else:

        breeds = db.execute("SELECT DISTINCT breed FROM dogs ORDER BY breed")
        colors = db.execute("SELECT DISTINCT color FROM dogs ORDER BY color")
        return render_template("index.html", breeds=breeds, colors=colors)

@app.route("/adddog")
@login_required
def adddog():
    """Add dog """

    if request.method == "POST":

        id_user = session["user_id"]

        dogName = request.form.get("name")
        status = request.form.get("status")
        location = request.form.get("location")
        breed = request.form.get("breed")
        color = request.form.get("color")
        pic = request.files

        if not status:
            errorMsg = "Must provide status!"
            return render_template("adddog.html", errorMsg=errorMsg)

        if not location:
            errorMsg = "Must provide location!"
            return render_template("adddog.html", errorMsg=errorMsg)

        if not breed:
            errorMsg = "Must provide breed!"
            return render_template("adddog.html", errorMsg=errorMsg)

        if not color:
            errorMsg = "Must provide color!"
            return render_template("adddog.html", errorMsg=errorMsg)
        
        

    else:
        return render_template("adddog.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        #Ensure username is provided
        if not request.form.get("username"):
            errorMsg = "Must provide username!"
            return render_template("register.html", errorMsg=errorMsg)

        #Ensure email is provided
        if not request.form.get("email"):
            errorMsg = "Must provide an email!"
            return render_template("register.html", errorMsg=errorMsg)

        #Ensure password is provided
        if not request.form.get("password"):
            errorMsg = "Must provide password!"
            return render_template("register.html", errorMsg=errorMsg)

        #Ensure confirm password is provided
        if not request.form.get("confirmation"):
            errorMsg = "Must confirm password!"
            return render_template("register.html", errorMsg=errorMsg)

        rows = db.execute("SELECT * FROM users WHERE username= :username", username=request.form.get("username"))

        #Check if username is taken
        if len(rows) != 0:
            errorMsg = "Username already taken!"
            return render_template("register.html", errorMsg=errorMsg)

        if request.form.get("password") != request.form.get("confirmation"):
            errorMsg = "Passwords do not match!"
            return render_template("register.html", errorMsg=errorMsg)

        #Insert new user in database
        db.execute("INSERT INTO users (username, hash, email) VALUES(:username, :password, :email)", username=request.form.get("username"),
        password=generate_password_hash(request.form.get("password")), email=request.form.get("email"))

        return render_template("login.html", username=request.form.get("username"), password=request.form.get("password"))
    else:
        return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            errorMsg = "Must provide username!"
            return render_template("login.html", errorMsg=errorMsg)

        # Ensure password was submitted
        if not request.form.get("password"):
            errorMsg = "Must provide password!"
            return render_template("login.html", errorMsg=errorMsg)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            errorMsg = "Invalid username and/or password!"
            return render_template("login.html", errorMsg=errorMsg)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():

    """ Edit username and password """

    if request.method == "POST":

        idUser = session["user_id"]

        row = db.execute("SELECT * FROM users WHERE id=:idUser", idUser=idUser)
        username = row[0]["username"]
        oldPassword = row[0]["hash"]
        newName = request.form.get("username")
        newPassword = request.form.get("newPassword")
        currentPassword = request.form.get("oldPassword")
        confirmation = request.form.get("confirmation")

        # Make sure that username is not taken
        if newName and newName != username:
            result = db.execute("SELECT * FROM users WHERE username=:username", username=newName)
            if len(result) != 0:
                errorMsg = "Username already taken!"
                return render_template("dashboard.html", errorMsg=errorMsg)

            # Update the users table with the new username
            db.execute("UPDATE users SET username=:username WHERE id=:idUser", username=newName, idUser=idUser)

        # Check if the user wants to change his password as well
        if not currentPassword and not newPassword and not confirmation:
            return redirect("/dashboard")
        else:

            # Make sure all password fields are filled
            if not currentPassword:
                errorMsg = "Must provide password!"
                return render_template("dashboard.html", errorMsg=errorMsg)
            if not newPassword:
                errorMsg = "Must provide new password!"
                return render_template("dashboard.html", errorMsg=errorMsg)
            if not confirmation or newPassword != confirmation:
                errorMsg = "Wrong confirm password!"
                return render_template("dashboard.html", errorMsg=errorMsg)
            if not check_password_hash(oldPassword, request.form.get("oldPassword")):
                errorMsg = "Wrong password!"
                return render_template("dashboard.html", errorMsg=errorMsg)

            # Insert the new hashed password in the table
            db.execute("UPDATE users SET hash=:hashP WHERE id=:idUser", hashP=generate_password_hash(newPassword), idUser=idUser)
            return redirect("/dashboard")

    else:
        # Check if user is logged in
        if not session["user_id"]:
            return redirect("/login")

        # Render the dashboard template if the request method is GET
        user = session["user_id"]
        row = db.execute("SELECT username FROM users WHERE id=:idUser", idUser = user)
        username = row[0]["username"]
        return render_template("dashboard.html", username=username)