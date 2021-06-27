# Python Imports
import datetime
import scipy.stats as stats
import matplotlib.pyplot as plt, mpld3
import matplotlib
matplotlib.use("TkAgg")
import numpy as np
import pandas as pd
import os

# Django Imports
from django.shortcuts import render
from django.http import HttpResponse

# Local Imports
from .models import User, Product, Review
from .management.commands.incentivized import Incentivized
from .management.commands.anomaly import Anomaly
from .management.commands.similarity import Similarity



def test(request):
    return HttpResponse("Hello World")



"""View function for home page of site."""
def index(request):
    # Generate counts of some of the main objects
    num_users = User.objects.all().count()
    num_products = Product.objects.all().count()
    num_reviews = Review.objects.all().count()

    context = {
        'num_users': num_users,
        'num_products': num_products,
        'num_reviews': num_reviews,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)



'''
    Parameters:
        (productASIN, objects you want to graph...)
'''
def plot(productASIN, duplicate, incentivized, anomaly):
    print("plot graphs")
    # create a graph
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(ncols=4, figsize=(11, 7))
    fig.subplots_adjust(wspace=0.4)
    
    duplicate.plot({"figure": fig, "axis": ax1}, productASIN)
    incentivized.plot({"figure": fig, "axis": ax2}, productASIN)
    anomaly.plot({"figure": fig, "axis": ax3}, productASIN)

    fig.show()
    fig.autofmt_xdate()
    fig_HTML = mpld3.fig_to_html(fig)
    return fig_HTML



# incentivizedReviews = Product.objects.filter(review__asin=productASIN).exclude(incentivizedRatio=0).count()
def result(request, productID):
    # static
    print("calculating similarity")
    duplicate = DetectionAlgorithms()
    duplicateRatio = duplicate.detect(productID)

    # Dynamic
    # Calculate Incentivized Ratio 
    print("calculating incentivized")
    incentivized = DetectionAlgorithms()
    incentivized.find_keywords()
    incentivizedRatio = incentivized.detect(productID)

    # Calculate Rating Anomaly Rate and Interval/range of review posting dates 
    print("calculating anomaly")
    r_anomaly = DetectionAlgorithms()
    r_scores = r_anomaly.detect(productID)
    reviewAnomalyRate = r_scores[0]
    ratingAnomalyRate = r_scores[1]

    # Create html product link
    link = ("https://www.amazon.com/dp/" + productID)

    # Calculate Number of Reviews for Given Product
    reviewsForProduct = Review.objects.all().filter(asin=productID).count()

    context = {
        'duplicateRatio': duplicateRatio,
        'incentivizedRatio': incentivizedRatio,
        'ratingAnomalyRate': ratingAnomalyRate,
        'reviewAnomalyRate': reviewAnomalyRate,
        'reviewsForProduct': reviewsForProduct,
        'link': link,
        'figure': figure,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'result.html', context=context)


