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
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.http import JsonResponse
from django.http import HttpResponseRedirect
from django.urls import reverse

# Local Imports
from .models import User, Product, Review
from .forms import AsinForm
from .management.commands.detection_algorithms import DetectionAlgorithms
from .management.commands.incentivized import Incentivized
from .management.commands.review_anomaly import ReviewAnomaly
from .management.commands.rating_anomaly import RatingAnomaly
from .management.commands.similarity import Similarity



"""View function for home page of site."""
def index(request):
    # Create a dropdown and text input form instances and populate them with data from the request (binding)
    asin_form = AsinForm(request.GET)

    # when a user types in the search box, autocomplete the first 10 product asin options from their input
    if request.method == 'GET':

        if asin_form.is_valid():
            # redirect to a new URL (result view):
            print("redirecting...")
            return HttpResponseRedirect(reverse('result', args=[asin_form.cleaned_data['asin_choice']]))
        
        # autocomplete feature
        if 'asin_id' in request.GET and request.GET['asin_id']:
            products = Product.objects.none()
            if 'category_id' in request.GET and request.GET['category_id']:
                products = Product.objects.filter(asin__istartswith=request.GET['asin_id'], category=request.GET['category_id'])
            else:
                products = Product.objects.filter(asin__istartswith=request.GET['asin_id'])
            
            max_count = 8
            current_count = 0
            titles = []
            # show first eight products that begin with user's input
            for product in products:
                if current_count < max_count:
                    titles.append(product.asin)
                    current_count += 1
                else:
                    break
            return JsonResponse(titles, safe=False)

    else:
        asin_form = AsinForm()

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', {"asin_form": asin_form})


def search_link(request):
    context = {
    
    }
    # Render the HTML template index.html with the data in the context variable
    return render(request, 'search_link.html', context)



"""View function for home page of site."""
def about(request):
    context = {
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'about.html', context=context)



#def get_color()

'''
    Parameters:
        (productASIN, objects you want to graph...)
'''
def plot(product_ASIN, duplicate, incentivized, review_anomaly, rating_anomaly):
    # create a graph
    plt.switch_backend('AGG')
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(ncols=4, figsize=(11, 7))
    fig.subplots_adjust(wspace=0.6)
    
    # plot all axes
    duplicate.plot(ax1)
    incentivized.plot(ax2)
    review_anomaly.plot(ax3)
    rating_anomaly.plot(ax4)

    # encode the figure as a png
    buf = BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    image_png = buf.getvalue()
    graph = base64.b64encode(image_png)
    graph = graph.decode('utf-8')
    buf.close()
    return graph



def result(request, product_ASIN):
    # static
    # Calculate Duplicate Ratio and number of duplicate reviews
    duplicate = Similarity()
    duplicateRatio = duplicate.detect(product_ASIN)
    totalDuplicate = Review.objects.filter(asin=product_ASIN, duplicate=1).count()

    # Dynamic
    # Calculate Incentivized Ratio and number of incentivized reviews
    incentivized = Incentivized()
    incentivizedRatio = incentivized.detect(product_ASIN)
    totalIncentivized = Review.objects.filter(asin=product_ASIN, incentivized=1).count()

    # Calculate Review Anomaly Rate and Interval/range of review posting dates 
    review_anomaly = ReviewAnomaly()
    reviewAnomalyRate = review_anomaly.detect(product_ASIN)
    totalReviewAnomalies = review_anomaly.review_anomalies

    # Calculate Rating Anomaly Rate and Interval/range of review posting dates 
    rating_anomaly = RatingAnomaly()
    ratingAnomalyRate = rating_anomaly.detect(product_ASIN)
    totalRatingAnomalies = rating_anomaly.rating_anomalies

    # Calculate Number of Reviews and Date Range for Given Product
    reviewsForProduct = Review.objects.filter(asin=product_ASIN).count()
    category = Product.objects.filter(asin=product_ASIN).values('category')[0]['category']

    # Plot graphs for each detection algorithm
    figure = plot(product_ASIN, duplicate, incentivized, review_anomaly, rating_anomaly)

    context = {
        'product_ASIN': product_ASIN,
        'category': category,
        
        'duplicateRatio': duplicateRatio,
        'totalDuplicate': totalDuplicate,

        'incentivizedRatio': incentivizedRatio,
        'totalIncentivized': totalIncentivized,

        'reviewAnomalyRate': reviewAnomalyRate,
        'totalReviewAnomalies': totalReviewAnomalies,

        'ratingAnomalyRate': ratingAnomalyRate,
        'totalRatingAnomalies': totalRatingAnomalies,
        
        'reviewsForProduct': reviewsForProduct,

        'figure': figure,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'result.html', context=context)



