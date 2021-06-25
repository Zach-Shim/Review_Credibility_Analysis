from django.db import models
from django.urls import reverse


class User(models.Model):
    # attributes
    reviewerID = models.TextField(primary_key=True)
    reviewerName = models.TextField()

    # Metadata
    class Meta:
        db_table = 'user'

    # Methods
    def get_absolute_url(self):
        """Returns the url to access a particular instance of MyModelName."""
        return reverse('model-detail-view', args=[str(self.reviewerID)])

    def __str__(self):
        """String for representing the MyModelName object (in Admin site etc.)."""
        return "UserID = " + self.reviewerID



'''
CREATE TABLE PRODUCT (
    asin                VARCHAR     NOT NULL
    category            VARCHAR     NOT NULL
    duplicateRatio      DECIMAL
    incentivizedRatio   DECIMAL
    ratingAnomalyRate   DECIMAL
    reviewAnomalyRate   DECIMAL
    PRIMARY KEY(asin)
);
'''
class Product(models.Model):
    # attributes
    asin = models.TextField(primary_key = True)
    category = models.TextField()
    duplicateRatio = models.DecimalField(max_digits=5, decimal_places=2, default = 0)
    incentivizedRatio = models.DecimalField(max_digits=5, decimal_places=2, default = 0)
    ratingAnomalyRate = models.DecimalField(max_digits=5, decimal_places=2, default = 0)
    reviewAnomalyRate = models.DecimalField(max_digits=5, decimal_places=2, default = 0)

    # Metadata
    class Meta:
        db_table = 'product'

    # Methods
    def get_absolute_url(self):
        """Returns the url to access a particular instance of MyModelName."""
        return reverse('model-detail-view', args=["https://www.amazon.com/dp/" + str(self.asin)])

    def __str__(self):
        """String for representing the MyModelName object (in Admin site etc.)."""
        return "Product Asin = " + self.asin



'''
CREATE TABLE REVIEW (
    userID              VARCHAR     NOT NULL
    asin                VARCHAR     NOT NULL
    reviewText          VARCHAR     NOT NULL
    overall             DECIMAL     NOT NULL
    unixReviewTime      INTEGER     NOT NULL
    primary key(reviewID, reviewerID, asin),
    foreign key(reviwerID) references User(userID) on delete cascade
    foreign key(asin) references Product(asin) on delete cascade
);
'''
class Review(models.Model):
    # foreign keys
    reviewerID = models.ForeignKey(User, on_delete = models.CASCADE, db_column = "reviewerID")
    asin = models.ForeignKey(Product, on_delete = models.CASCADE, db_column = "asin")

    # attributes
    reviewID = models.TextField(primary_key=True)
    reviewText = models.TextField()
    overall = models.IntegerField(choices = ((1, 1), (2, 2), (3, 3), (4, 4), (5, 5)))
    unixReviewTime = models.IntegerField()
    minHash = models.TextField(default="")

    # Metadata
    class Meta:
        db_table = 'review'
        constraints = [
            models.UniqueConstraint(fields=['reviewID', 'reviewerID', 'asin'], name='unique_review'),
        ]

    # Methods
    def get_absolute_url(self):
        """Returns the url to access a particular instance of MyModelName."""
        return reverse('model-detail-view', args=[str(self.reviewID)])

    def __str__(self):
        """String for representing the MyModelName object (in Admin site etc.)."""
        return "Review " + self.reviewID
