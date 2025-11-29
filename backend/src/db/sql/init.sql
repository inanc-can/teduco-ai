-- Run automatically by the Postgres container the first time it starts
-- Creates tables + an ENUM for document types

-- 1  Enum for allowed document types
CREATE TYPE document_type_enum AS ENUM ('transcript', 'vpd', 'cover_letter');

-- 2  Core user table
CREATE TABLE users (
    user_id       SERIAL PRIMARY KEY,
    user_fname    VARCHAR(50)  NOT NULL,
    user_lname    VARCHAR(50)  NOT NULL,
    -- we store only a *password hash* (bcrypt/argon2, etc.), never the raw password
    password_hash TEXT         NOT NULL,
    email         VARCHAR(255) NOT NULL UNIQUE,
    birth_date    DATE
);

-- 3  Master list of universities
CREATE TABLE universities (
    university_id SERIAL PRIMARY KEY,
    name          VARCHAR(255) NOT NULL,
    country       VARCHAR(100) NOT NULL,
    last_updated  TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 4  Junction table: which universities a user is interested in
CREATE TABLE user_universities (
    user_id       INT NOT NULL,
    university_id INT NOT NULL,
    PRIMARY KEY (user_id, university_id),
    FOREIGN KEY (user_id)       REFERENCES users(user_id)        ON DELETE CASCADE,
    FOREIGN KEY (university_id) REFERENCES universities(university_id) ON DELETE CASCADE
);

-- 5  Documents uploaded by users
CREATE TABLE documents (
    document_id   SERIAL PRIMARY KEY,
    user_id       INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    document_path TEXT NOT NULL,              -- path/URL to the stored file
    document_type document_type_enum NOT NULL,
    uploaded_at   TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
