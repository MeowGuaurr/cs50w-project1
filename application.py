import os

from flask import Flask, session, render_template, request, redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from flask import flash
import requests
import math
import string
import json

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
    if not session.get("logged_in"):
        return render_template("index.html")
    else:
        return render_template("search.html")


@app.route("/search", methods = ["POST", "GET"])
def search():
    if request.method == "POST":
        consulta =  str(request.form.get("books"))
        consulta = string.capwords(consulta, sep=None)
        print(consulta)

        if not consulta:
            flash("you must provide book information")
            return render_template("search.html")

        rows = db.execute("SELECT isbn, title, author, year FROM books WHERE isbn LIKE :consulta OR title LIKE :consulta OR author LIKE :consulta", {"consulta": "%" + consulta + "%"})

        result = rows.fetchall()
        print(result)

        if len(result) == 0:
            flash("could not find book")
            return render_template("search.html")


        return render_template("search.html", books=result)

    else:
        return render_template("search.html")

@app.route("/book/<isbn>", methods=['GET','POST'])
def book(isbn):
    if request.method =="POST":
        user = session["user_id"]

        rating = request.form.get("rating")
        comment= request.form.get("comment")

        rows = db.execute("SELECT book_id FROM books WHERE isbn = :isbn", {"isbn": isbn}) #selecciona id conforme a isbn
        bookid = rows.fetchone()
        book_id = bookid[0]
        print(book_id)

        row2 = db.execute("SELECT * FROM rate WHERE id_user = :id_user AND book_id = :book_id",
        {"id_user": user, "book_id" :book})

        if row2.rowcount == 1:
            flash("You already rate this book")
            return redirect("/book/" + isbn)

        rating =int(rating)

        db.execute("INSERT INTO rate (id_user, book_id, comment, rating) VALUES \
                    (:id_user, :book_id, :comment, :rating)",
                    {"id_user": user,
                    "book_id": book,
                    "comment": comment,
                    "rating": rating})

        db.commit()

        flash("comment submmited")
        return redirect("/book/" + isbn)

    else:

        consulta = db.execute("SELECT isbn, title, author, year FROM books WHERE \
                        isbn = :isbn",
                        {"isbn": isbn})
        resultado = consulta.fetchall()

        query = requests.get("https://www.googleapis.com/books/v1/volumes?q=isbn:"+isbn)
        response = query.json()

        response = response['items'][0]
        description = response["volumeInfo"]["description"]
        count = response["volumeInfo"]["ratingsCount"]
        rated = response["volumeInfo"]["averageRating"]

        resultado.append(response)

        # users

        row1 = db.execute("SELECT book_id FROM books WHERE isbn = :isbn", {"isbn":isbn})
        bookid = row1.fetchone()
        book_id = bookid[0]



        rates = db.execute("SELECT users.username, comment, rating, to_char(published_time, 'DD Mon YY - HH24:MI:SS') AS time FROM users INNER JOIN rate ON users.id_user = rate.id_user WHERE book_id = :book_id ORDER BY time ", {"book_id" : book_id})
        x = rates.fetchall()

        return render_template("book.html", consult=resultado, rates = x, description=description, count=count, rated=rated)

@app.route("/api/<isbn>", methods = ["GET", "POST"])
def api_route(isbn):
    libro = db.execute("SELECT * FROM books WHERE isbn = :isbn",
                        {"isbn": isbn})

    if libro.rowcount != 1:
        return jsonify({"Error": "Incorrect isbn"})

    req = requests.get("https://www.googleapis.com/books/v1/volumes?q=isbn:"+isbn)

    if req.status_code != 200:
        raise Exception("ERROR: unsuccesful API req")
    response = req.jason()
    response = response["items"][0]
    averageRating = response["volumeInfo"]["averageRating"]
    count= response["volumeInfo"]["ratingsCount"]

    return jsonify({
        "title": libro.title,
        "author": libro.author,
        "year": libro.year,
        "isbn": libro.isbn,
        "review_count": libro.count,
        "average_score": libro.averageRating})

@app.route("/login", methods = ["GET", "POST"])
def login():

    session.clear()

    if request.method == "POST":
        password = request.form.get("password")
        username = request.form.get("username")

        if not request.form.get("username"):
            flash("please write your username")
            return render_template("login.html")

        elif not request.form.get("password"):
            flash("please write your password")
            return render_template("login.html")

        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username": username})

        look = rows.fetchone()

        if look == None or not check_password_hash(look[2], password):
            flash("invalid username or password")
            return render_template("login.html")

        session["user_id"] = look[0]

        return render_template("search.html")

    else:
        return render_template("login.html")



@app.route("/logout")
def logout():
    session.clear()
    return render_template("index.html")

@app.route("/register", methods = ["POST", "GET"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            flash("please write a username")
            return render_template("register.html")

        if not password:
            flash("please write a password")
            return render_template("register.html")

        elif not confirmation:
            flash("please write password confirmation")
            return render_template("register.html")

        if password != confirmation:
            flash("password and confirmation do not match")
            return render_template("register.html")

        #valid_username = db.execute("SELECT * FROM users WHERE username LIKE :username",{"username": username}).fetchone()
        #if valid_username:
        #    flash("already registered")
         #   return redirect("login.html")

        password = generate_password_hash(password)
        Pass = db.execute("INSERT INTO users (username, password) VALUES (:username, :password);",{"username": username, "password": password})
        db.commit()
        flash(" already registered :)")

        return redirect("login")

    else:
        return render_template("register.html")