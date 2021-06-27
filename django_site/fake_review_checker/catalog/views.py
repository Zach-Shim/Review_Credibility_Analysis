# Python Imports
import datetime
import scipy.stats as stats
import matplotlib.pyplot as plt, mpld3
import matplotlib
matplotlib.use("TkAgg")
import numpy as np
import pandas as pd
import os

from io import BytesIO
import base64
import urllib

# Django Imports
from django.shortcuts import render
from django.http import HttpResponse

# Local Imports
from .models import User, Product, Review
from .management.commands.detection_algorithms import DetectionAlgorithms
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
def plot(product_ASIN, duplicate, incentivized, anomaly):
    # create a graph
    plt.switch_backend('AGG')
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(ncols=4, figsize=(11, 7))
    fig.subplots_adjust(wspace=0.4)
    
    duplicate.plot(ax1, product_ASIN)
    incentivized.plot(ax2, product_ASIN)
    anomaly.plot([ax3, ax4], product_ASIN)

    # encode the figure as a png
    buf = BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    image_png = buf.getvalue()
    graph = base64.b64encode(image_png)
    graph = graph.decode('utf-8')
    buf.close()
    return graph



# incentivizedReviews = Product.objects.filter(review__asin=productASIN).exclude(incentivizedRatio=0).count()
def result(request, product_ASIN):
    # static
    duplicate = Similarity()
    duplicateRatio = duplicate.detect(product_ASIN)

    # Dynamic
    # Calculate Incentivized Ratio 
    incentivized = Incentivized()
    incentivizedRatio = incentivized.detect(product_ASIN)

    # Calculate Rating Anomaly Rate and Interval/range of review posting dates 
    anomaly = Anomaly()
    (reviewAnomalyRate, ratingAnomalyRate) = anomaly.detect(product_ASIN)

    # Create html product link
    link = ("https://www.amazon.com/dp/" + product_ASIN)

    # Calculate Number of Reviews for Given Product
    reviewsForProduct = Review.objects.all().filter(asin=product_ASIN).count()

    figure = plot(product_ASIN, duplicate, incentivized, anomaly)

    context = {
        'product_ASIN': product_ASIN,
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


