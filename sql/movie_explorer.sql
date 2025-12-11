CREATE DATABASE IF NOT EXISTS movie_explorer
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE movie_explorer;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS principals;
DROP TABLE IF EXISTS ratings;
DROP TABLE IF EXISTS people;
DROP TABLE IF EXISTS movies;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE movies (
    tconst           VARCHAR(20) PRIMARY KEY,
    titleType        VARCHAR(50),
    primaryTitle     VARCHAR(255),
    originalTitle    VARCHAR(255),
    isAdult          INT,
    startYear        INT,
    endYear          INT,
    runtimeMinutes   INT,
    genres           VARCHAR(255)
);

CREATE TABLE ratings (
    tconst         VARCHAR(20) PRIMARY KEY,
    averageRating  DECIMAL(3,1),
    numVotes       INT,
    CONSTRAINT fk_ratings_movie
        FOREIGN KEY (tconst) REFERENCES movies(tconst)
);

CREATE TABLE people (
    nconst             VARCHAR(20) PRIMARY KEY,
    primaryName        VARCHAR(255),
    birthYear          INT,
    deathYear          INT,
    primaryProfession  VARCHAR(255),
    knownForTitles     VARCHAR(500)
);

CREATE TABLE principals (
    tconst     VARCHAR(20),
    ordering   INT,
    nconst     VARCHAR(20),
    category   VARCHAR(100),
    job        VARCHAR(255),
    characters VARCHAR(500),
    PRIMARY KEY (tconst, ordering),
    CONSTRAINT fk_principals_movie
        FOREIGN KEY (tconst) REFERENCES movies(tconst),
    CONSTRAINT fk_principals_person
        FOREIGN KEY (nconst) REFERENCES people(nconst)
);