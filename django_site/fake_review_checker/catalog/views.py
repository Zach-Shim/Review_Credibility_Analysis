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
from .management.commands.anomaly import Anomaly
from .management.commands.similarity import Similarity



"""View function for home page of site."""
def index(request):
    # when a user types in the search box, autocomplete the first 10 product asin options from their input
    if 'term' in request.GET:
        titles = [product.asin for product in Product.objects.filter(asin__istartswith=request.GET.get('term'))]
        return JsonResponse(titles[0:10], safe=False)

    if request.method == 'GET':
        # Create a form instance and populate it with data from the request (binding):
        form = AsinForm(request.GET)
        if form.is_valid():
            # redirect to a new URL:
            return HttpResponseRedirect(reverse('result', args=[form.cleaned_data['asin_choice']]) )


    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html')



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
def plot(product_ASIN, duplicate, incentivized, anomaly):
    # create a graph
    plt.switch_backend('AGG')
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(ncols=4, figsize=(11, 7))
    fig.subplots_adjust(wspace=0.6)
    
    duplicate.plot(ax1)
    incentivized.plot(ax2)
    anomaly.plot([ax3, ax4])

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

    # Calculate Rating Anomaly Rate and Interval/range of review posting dates 
    anomaly = Anomaly()
    (reviewAnomalyRate, ratingAnomalyRate) = anomaly.detect(product_ASIN)
    reviewDayRange = anomaly.get_day_range()
    totalReviewAnomalies = len(anomaly.review_count_anomalies['anoms']['anoms'])
    totalRatingAnomalies = len(anomaly.rating_value_anomalies['anoms']['anoms'])

    # Calculate Number of Reviews and Date Range for Given Product
    reviewsForProduct = Review.objects.filter(asin=product_ASIN).count()
    category = Product.objects.filter(asin=product_ASIN).values('category')[0]['category']

    # Plot graphs for each detection algorithm
    figure = plot(product_ASIN, duplicate, incentivized, anomaly)

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
        'reviewDayRange': reviewDayRange,

        'figure': figure,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'result.html', context=context)



