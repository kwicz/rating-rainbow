CREATE TABLE books (
	id SERIAL PRIMARY KEY,
	title VARCHAR NOT NULL,
	author VARCHAR NOT NULL,
	year VARCHAR NOT NULL,
	isbn VARCHAR NOT NULL
);

CREATE TABLE users (
	id SERIAL PRIMARY KEY,
	username TEXT UNIQUE,
	hash TEXT NOT NULL,
	reviewed VARCHAR
);

CREATE TABLE reviews (
	id SERIAL PRIMARY KEY,
	user_id INT NOT NULL,
	book_id INT NOT NULL,
	rating INT,
	comment VARCHAR
);