-- =========================================================
-- analysis_queries.sql
-- Movie Explorer Project - Analytical SQL Queries
-- Theme: High-Quality Movies & Top Talent Explorer
-- =========================================================

-- Use the project database
USE movie_explorer;

-- =========================================================
-- 0. VIEW: Movie + Ratings
--    This view combines movies and ratings for easier analysis.
-- =========================================================

CREATE OR REPLACE VIEW vw_movie_ratings AS
SELECT
    m.tconst,
    m.primaryTitle,
    m.originalTitle,
    m.titleType,
    m.startYear,
    m.runtimeMinutes,
    m.genres,
    r.averageRating,
    r.numVotes
FROM movies  AS m
LEFT JOIN ratings AS r
    ON m.tconst = r.tconst;


-- =========================================================
-- 1. JOIN Query #1:
--    Top 20 highest-rated movies with enough votes.
--    Uses the view (movies + ratings).
-- =========================================================

SELECT
    v.primaryTitle,
    v.startYear,
    v.genres,
    v.averageRating,
    v.numVotes
FROM vw_movie_ratings AS v
WHERE v.averageRating IS NOT NULL
  AND v.averageRating >= 8.0
  AND v.numVotes >= 500
  AND v.startYear <> -1
ORDER BY v.averageRating DESC, v.numVotes DESC
LIMIT 20;


-- =========================================================
-- 2. JOIN Query #2 + GROUP BY #1:
--    Top directors by average rating (minimum 3 movies).
--    Joins principals + people + movies + ratings.
-- =========================================================

SELECT
    p.primaryName AS directorName,
    COUNT(*)      AS movieCount,
    AVG(r.averageRating) AS avgRating
FROM principals AS pr
JOIN people     AS p  ON pr.nconst = p.nconst
JOIN movies     AS m  ON pr.tconst = m.tconst
JOIN ratings    AS r  ON m.tconst = r.tconst
WHERE pr.category = 'director'
  AND r.averageRating IS NOT NULL
  AND r.numVotes >= 200
  AND m.startYear <> -1
GROUP BY p.primaryName
HAVING COUNT(*) >= 3
ORDER BY avgRating DESC, movieCount DESC
LIMIT 20;


-- =========================================================
-- 3. JOIN Query #3 + GROUP BY #2:
--    Actors/actresses who frequently appear in
--    better-than-average movies (relative to global average).
-- =========================================================

WITH avg_rating AS (
    SELECT AVG(averageRating) AS global_avg
    FROM ratings
    WHERE averageRating > 0
)

SELECT
    p.primaryName AS actorName,
    COUNT(DISTINCT m.tconst) AS movieCount,
    AVG(r.averageRating)     AS avgActorRating
FROM principals AS pr
JOIN people     AS p  ON pr.nconst = p.nconst
JOIN movies     AS m  ON pr.tconst = m.tconst
JOIN ratings    AS r  ON m.tconst = r.tconst
CROSS JOIN avg_rating ar
WHERE pr.category IN ('actor', 'actress')
  AND r.averageRating > ar.global_avg      -- only above-average movies
  AND r.averageRating > 0
  AND m.startYear <> -1
GROUP BY p.primaryName
HAVING COUNT(DISTINCT m.tconst) >= 2       -- at least 2 such movies
ORDER BY movieCount DESC, avgActorRating DESC
LIMIT 20;


-- =========================================================
-- 4. CTE / Subquery:
--    Directors whose average rating is above the global average.
--    Uses two CTEs: overall_avg and director_avg.
-- =========================================================

WITH overall_avg AS (
    SELECT AVG(averageRating) AS global_avg
    FROM ratings
    WHERE averageRating > 0
),
director_avg AS (
    SELECT
        p.primaryName AS directorName,
        AVG(r.averageRating) AS director_avg_rating,
        COUNT(*) AS movieCount
    FROM principals AS pr
    JOIN people  AS p ON pr.nconst = p.nconst
    JOIN movies  AS m ON pr.tconst = m.tconst
    JOIN ratings AS r ON m.tconst = r.tconst
    WHERE pr.category = 'director'
      AND r.averageRating > 0
      AND m.startYear <> -1
    GROUP BY p.primaryName
)
SELECT
    d.directorName,
    d.movieCount,
    d.director_avg_rating,
    o.global_avg
FROM director_avg AS d
CROSS JOIN overall_avg AS o
WHERE d.director_avg_rating > o.global_avg
ORDER BY d.director_avg_rating DESC, d.movieCount DESC
LIMIT 20;


-- =========================================================
-- 5. Stored Procedure:
--    GetTopMoviesByGenreYear
--    Returns top movies for a given genre and minimum year/votes.
-- =========================================================

DROP PROCEDURE IF EXISTS GetTopMoviesByGenreYear;
DELIMITER //

CREATE PROCEDURE GetTopMoviesByGenreYear (
    IN p_genre     VARCHAR(50),
    IN p_min_year  INT,
    IN p_min_votes INT
)
BEGIN
    SELECT
        m.primaryTitle,
        m.startYear,
        m.genres,
        r.averageRating,
        r.numVotes
    FROM movies  AS m
    JOIN ratings AS r
      ON m.tconst = r.tconst
    WHERE m.startYear >= p_min_year
      AND m.startYear <> -1
      AND r.numVotes   >= p_min_votes
      AND r.averageRating IS NOT NULL
      AND m.genres LIKE CONCAT('%', p_genre, '%')
    ORDER BY r.averageRating DESC, r.numVotes DESC
    LIMIT 50;
END //

DELIMITER ;

-- Example call
CALL GetTopMoviesByGenreYear('Action', 2000, 500);

