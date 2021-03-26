import os

from flask import Flask, session, render_template, request, redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


app = Flask(__name__)

# Check for environment variable
if not "postgres://aigpbdyoxbwzjl:a88f1dbaca1b4b3f421c70e9ecce974162164c0e20e930cb0ce68f37ad80aa16@ec2-54-162-119-125.compute-1.amazonaws.com:5432/d7jd4p47r9c69":
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine("postgres://aigpbdyoxbwzjl:a88f1dbaca1b4b3f421c70e9ecce974162164c0e20e930cb0ce68f37ad80aa16@ec2-54-162-119-125.compute-1.amazonaws.com:5432/d7jd4p47r9c69")
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("index.html")

@app.route("layout")
def layout():
    return render_template("layout.html")


@app.route("login.html", methods = ["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if not request.form.get("username"):
            error = 'must provide username'

        elif not request.form.get("password"):
            error = 'must provide password'

        rows = db.execute("SELECT username FROM users WHERE username = :username", username = request.form.get("username"))
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            error = 'invalid username and/or password'

        session["user_id"] = rows[0]["id"]

        return redirect("/")

    else:
        return render_template("login.html")



@app.route("/register", methods = ["POST", "GET"])
def register():
    if request.method == "POST":
        if not request.form.get("username"):
            error = 'You must provide a username.'

        if not request.form.get("password"):
            error = 'You must provide a password'

        elif not request.form.get("confirmation"):
            error = 'You must confirm your password'

        if (request.form.get("password")) != (request.form.get("confirmation")):
            error = 'Password do not match'

        Hash = generate_password_hash(request.form.get("password"))
        Pass = db.execute("INSERT INTO users (username, hash) VALUES (:username, :Hash", username = request.form.get("username"), Hash = Hash)

        if not Pass:
            error = 'Already registered'

        sesion["user_id"] = nuevo

        return render_template("login.html")

    else:
        return render_template("register.html")