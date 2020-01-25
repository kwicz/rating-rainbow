import os
import requests
import datetime

from flask import Flask, session, request, render_template, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import default_exceptions
from PIL import Image
from io import BytesIO

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Forget any user_id
        session.clear()

        # Ensure username was submitted
        if not request.form.get("username"):
                    return render_template("apology.html", message="Please provide username.")

        # Ensure password was submitted
        elif not request.form.get("password"):
                    return render_template("apology.html", message="Please provide password.")

        username = request.form.get("username")
        password = request.form.get("password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username":username}).fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
                    return render_template("apology.html", message="Invalid username and/or password.")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]

        # Redirect user to home page
        return render_template("search.html")

    # User reached route via GET (as by clicking a link or via redirect)
    else:

        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return render_template("home.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Forget any user_id
        session.clear()

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure username was submitted
        if not username:
                    return render_template("apology.html", message="Please provide username.")

        # Ensure password was submitted
        elif not password:
                    return render_template("apology.html", message="Please provide password.")

        # Ensure password confirmation was submitted
        elif not confirmation:
                    return render_template("apology.html", message="Please provide password confirmation.")

        # Ensure password and confirmation match
        elif password != confirmation:
                    return render_template("apology.html", message="Password must match confirmation.")

        # Hash password
        password_hash = generate_password_hash(password)

        # Ensure username is unique
        result = db.execute("INSERT INTO users (username, hash) VALUES(:username, :password_hash)",
                            {"username":username, "password_hash":password_hash})
        db.commit()

        # If not unique...
        if not result:
            return render_template("apology.html", message="Username not valid.")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username":username}).fetchall()

        # Log user in automatically
        session["user_id"] = rows[0]["id"]


        # Head to logged in page
        return render_template("search.html")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/search", methods=["GET", "POST"])
def search():
    """Allow user to search for a book."""

    #User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        
        #Recieve search term from user 
        query = request.form.get("query")

        query = "%" + query + "%"

        #Check books table for search term
        books = db.execute("SELECT * FROM books WHERE title LIKE :query OR author LIKE :query OR year LIKE :query OR isbn LIKE :query",
            {"query":query}).fetchall()

        #Return error page if no books exist.
        if len(books) == 0:
            return render_template("apology.html", message="No books with that information could be found.")

        #Request book cover images from Open Library API.
        data = {}
        results = []
        for book in books:
            title = str(book.title)
            author = str(book.author)
            key = "ISBN"
            value = book.isbn
            cover = str("http://covers.openlibrary.org/b/" + key + "/" + value + "-M.jpg")
            data = {"title": title, "author": author, "cover": cover, "id": str(book.id)}
            results.append(data)

        return render_template("results.html", results=results)
    # User reached route via GET (as by clicking a link or via redirect)    
    else:
        return render_template("search.html")

@app.route("/bookpage/<int:book_id>", methods=["GET", "POST"])
def bookpage(book_id):
    """List details about a single book."""

    if request.method == "GET":

        #Find book by id in books table.
        book = db.execute("SELECT * FROM books WHERE id = :id", 
            {"id": book_id}).fetchone()
        if book is None:
            return render_template("apology.html", message="Book does not exist.")

        #Request ratings data from Goodreads API.    
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "fB5hPbaGNes1ZC0CNFCrQ", "isbns": book.isbn})
        if res.status_code != 200:
            raise Exception("ERROR: API request unsuccessful.")
        data = res.json()
        average_rating = data["books"][0]["average_rating"]
        ratings_count = data["books"][0]["work_ratings_count"]
        
        #Gather user reviews from reviews table.
        reviews = db.execute("SELECT * FROM reviews WHERE book_id = :book_id",
            {"book_id": book_id}).fetchall()

        #Check if user has already reviewed book.
        user_id = session["user_id"]

        reviewed = db.execute("SELECT * FROM reviews WHERE user_id = :user_id AND book_id = :book_id", {"user_id": user_id, "book_id": book_id}).fetchall()

        #Request book cover image from Open Library API.
        key = "ISBN"
        value = book.isbn
        cover = "http://covers.openlibrary.org/b/" + key + "/" + value + "-M.jpg"

        #Send book data to html page.
        return render_template("bookpage.html", book=book, average_rating=average_rating, ratings_count=ratings_count, reviews=reviews, cover=cover, reviewed=reviewed)

    else:
        
        #Pass data from html form into reviews database.
        book = db.execute("SELECT * FROM books WHERE id = :id", {"id": book_id}).fetchone()
        user_id = session["user_id"]
        rating = request.form.get("user_rating")
        review = request.form.get("user_review")
        book_id = book.id

        user_review = db.execute("INSERT INTO reviews (user_id, rating, comment, book_id) VALUES (:user_id, :rating, :review, :book_id)",
            {"user_id":user_id, "rating":rating, "review":review, "book_id":book_id})
        db.commit()

        return render_template("thankyou.html", book=book)

@app.route("/results")
def results():
    return render_template("results.html")

@app.route("/thankyou")
def thankyou():
    return render_template("thankyou.html")

@app.route("/apology")
def apology():
    return render_template("apology.html")

@app.route("/api/<book_isbn>")
def api(book_isbn):
    """Return details about a single book."""

    #Find book data using ISBN in books table.
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": book_isbn}).fetchone()
    
    #Request ratings data from Goodreads API.    
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "fB5hPbaGNes1ZC0CNFCrQ", "isbns": book.isbn})
    if res.status_code != 200:
        raise Exception("ERROR: API request unsuccessful.")
    data = res.json()
    
    #Set variables from Goodreads data.
    average_score = data["books"][0]["average_rating"]
    review_count = data["books"][0]["work_ratings_count"]

    return jsonify({
        "title": book.title,
        "author": book.author,
        "year": book.year,
        "isbn": book.isbn,
        "review_count": review_count,
        "average_score": average_score
        })
