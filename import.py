import os
import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))

db = scoped_session(sessionmaker(bind=engine))

f = open("books.csv")
reader = csv.reader(f)

# Name each column.
for isbn, title, author, year in reader:
	
	# Place values from CSV line into SQL command.
	db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
		{"isbn": isbn, "title": title, "author":author, "year":year})
	
	# Confirm titles are added.
	print(f"Added {title} to books database.")

# Close the transaction.
db.commit()