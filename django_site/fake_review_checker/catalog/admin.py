from django.contrib import admin
from .models import User, Product, Review

#admin.site.register(User)
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('reviewerID', 'reviewerName')


#admin.site.register(Product)
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('asin', 'category', 'duplicateRatio', 'incentivizedRatio', 'ratingAnomalyRate', 'reviewAnomalyRate')


#admin.site.register(Review)
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('reviewerID', 'asin', 'reviewText', 'overall', 'unixReviewTime')
