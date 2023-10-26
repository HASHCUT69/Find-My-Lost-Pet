import smtplib
import random
import os
import time
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
app.config["UPLOAD_FOLDER"] = "C:/Users/saiki/Desktop/LostPet/Find-My-Lost-Pet/static/pics"
app.config["MAX_CONTENT_PATH"] = 5000000

Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///project.db")


@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":

        # Get user search input such as status, location, breed, color of the dog
        status = request.form.get("status")
        location = request.form.get("location")
        breed = request.form.get("breed")
        color = request.form.get("color")

        # Get existing colors and breeds from the database
        locations = db.execute(
            "SELECT DISTINCT location FROM dogs ORDER BY location")
        breeds = db.execute("SELECT DISTINCT breed FROM dogs ORDER BY breed")
        colors = db.execute("SELECT DISTINCT color FROM dogs ORDER BY color")

        # Check if status is provided
        if not status:
            errorMsg = "Must provide status!"
            return render_template("index.html", errorMsg=errorMsg, breeds=breeds, colors=colors, locations=locations)

        # Check if location is provided
        if not location:
            errorMsg = "Must provide location!"
            return render_template("index.html", errorMsg=errorMsg, breeds=breeds, colors=colors, locations=locations)

        # Check if breed is provided
        # if not breed:
        #     errorMsg = "Must provide breed!"
        #     return render_template("index.html", errorMsg=errorMsg, breeds=breeds, colors=colors)

        # # Check if color is provided
        # if not color:
        #     errorMsg = "Must provide color!"
        #     return render_template("index.html", errorMsg=errorMsg, breeds=breeds, colors=colors)

        # Search for the lost/found dog in the database
        rows = db.execute("SELECT username, email, dog_name, status, location, picture, breed, color FROM dogs JOIN users ON dogs.id_user = users.id WHERE status = :status AND location = :location AND (:breed IS NULL OR breed = :breed) AND (:color IS NULL OR color = :color);",
                          status=status, location=location, breed=breed, color=color)
        counter = 0

        # Return result and load the existing colors and breeds in select menus in the search form
        return render_template("index.html", rows=rows, breeds=breeds, colors=colors, locations=locations, counter=counter)

    else:

        # Get existing colors and breeds from the database
        breeds = db.execute("SELECT DISTINCT breed FROM dogs ORDER BY breed")
        colors = db.execute("SELECT DISTINCT color FROM dogs ORDER BY color")
        locations = db.execute(
            "SELECT DISTINCT location FROM dogs ORDER BY location")
        breeds = db.execute("SELECT DISTINCT breed FROM dogs ORDER BY breed")
        # Load the existing colors and breeds in select menus in the search form
        return render_template("index.html", breeds=breeds, colors=colors, locations=locations)


@app.route("/mydogs")
@login_required
def mydogs():
    user_id = session["user_id"]

    # Find all dogs added by the user
    rows = db.execute(
        "SELECT * FROM dogs WHERE id_user=:user_id", user_id=user_id)

    # Return template with all the dogs added by the user
    return render_template("mydogs.html", rows=rows)


@app.route("/adddog", methods=["GET", "POST"])
@login_required
def adddog():
    """Add dog """

    if request.method == "POST":

        id_user = session["user_id"]

        # Get name, status, breed, color and picture of the dog to be added
        dogName = request.form.get("name")
        status = request.form.get("status")
        location = request.form.get("location")
        breed = request.form.get("breed")
        color = request.form.get("color")
        pic = request.files["pic"]

        # Check if status is given
        if not status:
            errorMsg = "Must provide status!"
            return render_template("adddog.html", errorMsg=errorMsg)

        # Check if location is given
        if not location:
            errorMsg = "Must provide location!"
            return render_template("adddog.html", errorMsg=errorMsg)

        # Check if breed is given
        if not breed:
            # errorMsg = "Must provide breed!"
            # return render_template("adddog.html", errorMsg=errorMsg)
            breed = "NA"

        # Check if color is given
        if not color:
            errorMsg = "Must provide color!"
            return render_template("adddog.html", errorMsg=errorMsg)

        # Check if image is uploaded by the user
        if pic.filename == '':
            errorMsg = "Must provide a picture"
            return render_template("adddog.html", errorMsg=errorMsg)

        # Get the image name to save it with the file path in the db
        picName = secure_filename(pic.filename)

        # Save picture in a folder on the server
        pic.save(os.path.join(app.config["UPLOAD_FOLDER"], picName))

        # Upload name, status, breed, color and picture of the dog in the db
        db.execute("INSERT INTO dogs (id_user, dog_name, status, location, picture, breed, color) VALUES(:id_user, :dogName, :status, :location, :picture, :breed, :color)",
                   id_user=id_user, dogName=dogName, status=status, location=location, picture=picName, breed=breed, color=color)

        flash("Success! Dog added.")
        return redirect("/mydogs")

    else:
        return render_template("adddog.html")


@app.route("/delete", methods=["POST"])
def delete():
    # get the id of the dog that has to be deleted
    dogId = request.form.get("dogId")
    db.execute("DELETE FROM dogs WHERE id_dog=:dogId", dogId=dogId)

    # Redirect to the updated mydogs page
    return redirect("/mydogs")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        # Ensure username is provided
        if not request.form.get("username"):
            errorMsg = "Must provide username!"
            return render_template("register.html", errorMsg=errorMsg)

        # Ensure email is provided
        if not request.form.get("email"):
            errorMsg = "Must provide an email!"
            return render_template("register.html", errorMsg=errorMsg)

        # Ensure password is provided
        if not request.form.get("password"):
            errorMsg = "Must provide password!"
            return render_template("register.html", errorMsg=errorMsg)

        # Ensure confirm password is provided
        if not request.form.get("confirmation"):
            errorMsg = "Must confirm password!"
            return render_template("register.html", errorMsg=errorMsg)

        rows = db.execute("SELECT * FROM users WHERE username= :username",
                          username=request.form.get("username"))

        emailRows = db.execute("SELECT * FROM users WHERE email= :email",
                               email=request.form.get("email"))
        
        # Check if username is taken
        if len(rows) != 0:
            errorMsg = "Username already taken!"
            return render_template("register.html", errorMsg=errorMsg)
        # Check if username is taken
        if len(emailRows) != 0:
            errorMsg = "Email already used!"
            return render_template("register.html", errorMsg=errorMsg)

        # Check if passwords match
        if request.form.get("password") != request.form.get("confirmation"):
            errorMsg = "Passwords do not match!"
            return render_template("register.html", errorMsg=errorMsg)

        # Insert new user in database
        db.execute("INSERT INTO users (username, hash, email) VALUES(:username, :password, :email)", username=request.form.get("username"),
                   password=generate_password_hash(request.form.get("password")), email=request.form.get("email"))

        # Show the login page with the user credentials in the fields
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

        # Find user in the db by id
        row = db.execute("SELECT * FROM users WHERE id=:idUser", idUser=idUser)
        username = row[0]["username"]
        oldPassword = row[0]["hash"]
        newName = request.form.get("username")
        newPassword = request.form.get("newPassword")
        currentPassword = request.form.get("oldPassword")
        confirmation = request.form.get("confirmation")

        # Make sure that username is not taken
        if newName and newName != username:
            result = db.execute(
                "SELECT * FROM users WHERE username=:username", username=newName)
            if len(result) != 0:
                errorMsg = "Username already taken!"
                return render_template("dashboard.html", errorMsg=errorMsg)

            # Update the users table with the new username
            db.execute("UPDATE users SET username=:username WHERE id=:idUser",
                       username=newName, idUser=idUser)

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
            db.execute("UPDATE users SET hash=:hashP WHERE id=:idUser",
                       hashP=generate_password_hash(newPassword), idUser=idUser)
            return redirect("/dashboard")

    else:
        # Check if user is logged in
        if not session["user_id"]:
            return redirect("/login")

        # Render the dashboard template if the request method is GET
        user = session["user_id"]
        row = db.execute(
            "SELECT username FROM users WHERE id=:idUser", idUser=user)
        username = row[0]["username"]
        return render_template("dashboard.html", username=username)

@app.route("/getmail", methods=["GET", "POST"])
def getmail():
    if request.method == "POST":
       email = request.form.get("email")
        # Find user in the db by id
       row1 = db.execute("SELECT * FROM users WHERE email=:email", email=email)
       if(len(row1)==0):
            errorMsg = "Email address not found!"
            return render_template("getmail.html", errorMsg=errorMsg)
       return redirect("/forgotpassword")
    else:
        return render_template("getmail.html") 


@app.route("/forgotpassword", methods=["GET", "POST"])
def forgotpassword():
    """ Edit username and password """

    if request.method == "POST":
        # Find user in the db by id
        
        row = db.execute("SELECT * FROM users WHERE email=:email", email="saikiransk6342@gmail.com")  
        def generate_otp():
            return str(random.randint(100000, 999999))

        sender_email = "lostpetconnect886@gmail.com"
        sender_password = "woxzsrgqyduderyo"

        try:
            smtp_server = smtplib.SMTP("smtp.gmail.com", 587)
            smtp_server.starttls()
            smtp_server.login(sender_email, sender_password)

            recipient_email = "saikiransk6342@gmail.com"
            otp = "891534"

            subject = "Your OTP Code"
            body = f"Your OTP code is: {otp}"

            message = f"Subject: {subject}\n\n{body}"

            smtp_server.sendmail(sender_email, recipient_email, message)
            print("OTP sent successfully!")
            smtp_server.quit()
        except Exception as e:
            print(f"Failed to send OTP: {e}")        




        username = row[0]["username"]
        oldPassword = row[0]["hash"]
        newPassword = request.form.get("newPassword")
        confirmation = request.form.get("confirmation")
        otpEntered=request.form.get("otp")

        # Check if the user wants to change his password as well
        if  not newPassword and not confirmation:
            return redirect("/forgotpassword")
        else:

            # Make sure all password fields are filled
            if str(otp)!=str(otpEntered):
                errorMsg = "OTP Incorrect !!!"+otp+"   "+otpEntered
                return render_template("forgotpassword.html", errorMsg=errorMsg)
            if not newPassword:
                errorMsg = "Must provide  password!"
                return render_template("forgotpassword.html", errorMsg=errorMsg)
            if not confirmation or newPassword != confirmation:
                errorMsg = "Passwords mismatch!!!"
                return render_template("forgotpassword.html", errorMsg=errorMsg)
            # Insert the new hashed password in the table
            db.execute("UPDATE users SET hash=:hashP WHERE email=:email",
                       hashP=generate_password_hash(newPassword), email="saikiransk6342@gmail.com")
            return redirect("/login")

    else:
        
        return render_template("forgotpassword.html")


if __name__ == '__main__':
    app.run(debug=True)
