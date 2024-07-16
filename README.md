## Description:
This repository hosts open-source code for an Amazon fake review checker.
Spam and false advertisement are rampant on Amazon, where bots will fill a product with fake positive/negative reivews.
This negatively impacts both shoppers and sellers.

This projects is a web app that takes an Amazon product link from the user and implements a machine learning pipeline 

## System Architecture
Model-View-Controller (MVC) architectural pattern. 

View:
  User picks a product to detect fake reviews for. 

Controller:
  Uses machine learning algorithms to determine validity of reviews for a product.
  The system architecture is broken into three lowly coupled parts:
  1.	Detection of duplicate reviews
  2.	Detection of anomaly in review count and rating distribution
  3.	Detection of incentivized reviews 

Model:
  A credibility score is generated and displayed to the user. 

## Tech Stack
•	Backend:
  o	Django
  o	Python
  o	SQLite3

•	Frontend:
  o	HTML5
  o	CSS
  o	Javascript

Application:
- Any small or large business that displays reviews on their website.
- Plagiarism detection.
