Create model Product
CREATE TABLE "product" (
	"asin" text NOT NULL PRIMARY KEY, 
	"category" text NOT NULL, 
	"duplicateRatio" decimal NOT NULL, 
	"incentivizedRatio" decimal NOT NULL, 
	"ratingAnomalyRate" decimal NOT NULL, 
	"reviewAnomalyRate" decimal NOT NULL
);

Create model User
CREATE TABLE "user" (
	"userID" text NOT NULL PRIMARY KEY, 
	"username" text NOT NULL
);

Create model Review
CREATE TABLE "review" (
	"reviewID" int NOT NULL PRIMARY KEY,
	"reviewText" text NOT NULL, 
	"overall" decimal NOT NULL, 
	"unixReviewTime" integer NOT NULL check(unixReviewTime in (1, 2, 3, 4, 5),
	"minHash" text NOT NULL, 
	“duplicate” int NOT NULL check (duplicate = 0 or duplicate = 1),
	“incentivized” int NOT NULL check (incentivized = 0 or incentivized = 1),
	"asin" text NOT NULL REFERENCES "product" ("asin") DEFERRABLE INITIALLY DEFERRED, 
	"reviewerID" text NOT NULL REFERENCES "user" ("userID") DEFERRABLE INITIALLY DEFERRED,
	UNIQUE(reviewID, asin, reviewerID)
);
