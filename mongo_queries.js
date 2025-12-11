/* * MongoDB Aggregation & Queries for Movie Explorer
 * Part 1: ETL Pipeline to create 'movies_master' collection
 */

// 1. Data Cleaning & Denormalization Pipeline
// (Run this in Aggregation tab of 'raw_titles')
[
  {
    $match: {
      startYear: { $ne: "\\N" },
      genres: { $ne: "\\N" }
    }
  },
  {
    $addFields: {
      startYear: { $toInt: "$startYear" },
      genresArray: { $split: ["$genres", ","] }
    }
  },
  {
    $lookup: {
      from: "raw_ratings",
      localField: "tconst",
      foreignField: "tconst",
      as: "rating_info"
    }
  },
  {
    $lookup: {
      from: "raw_principals",
      localField: "tconst",
      foreignField: "tconst",
      as: "cast_info"
    }
  },
  {
    $project: {
      _id: 0,
      movieId: "$tconst",
      title: "$primaryTitle",
      year: "$startYear",
      genres: "$genresArray",
      rating: { $toDouble: { $arrayElemAt: ["$rating_info.averageRating", 0] } },
      votes: { $toInt: { $arrayElemAt: ["$rating_info.numVotes", 0] } },
      cast: "$cast_info"
    }
  },
  {
    $out: "movies_master"
  }
]

/* * Part 2: Analytical Queries
 */

// Query 1: Filter High Rated Recent Movies
// db.movies_master.find({ "year": { "$gt": 2015 }, "rating": { "$gt": 7.0 } })

// Query 2: Text Search for "Love"
// db.movies_master.createIndex({ title: "text" })
// db.movies_master.find({ "$text": { "$search": "Love" } })

// Query 3: Aggregation - Average Rating by Genre
/*
[
  { $unwind: "$genres" },
  { $group: { _id: "$genres", avgRating: { $avg: "$rating" }, count: { $sum: 1 } } },
  { $sort: { avgRating: -1 } },
  { $match: { count: { $gt: 5 } } }
]
*/