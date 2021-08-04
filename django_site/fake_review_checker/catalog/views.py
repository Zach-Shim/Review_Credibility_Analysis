# Python Imports
import scipy.stats as stats
import matplotlib.pyplot as plt, mpld3
import matplotlib
matplotlib.use("TkAgg")
import numpy as np
import pandas as pd

from io import BytesIO
import base64
import urllib

# Django Imports
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.http import JsonResponse
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic

# Local Imports
from .models import User, Product, Review
from .forms import AsinForm, LinkForm
from .management.commands.detection_algorithms import DetectionAlgorithms
from .management.commands.incentivized import Incentivized
from .management.commands.review_anomaly import ReviewAnomaly
from .management.commands.rating_anomaly import RatingAnomaly
from .management.commands.similarity import Similarity
from .management.commands.svm import SVM
from .management.commands.lsi import LSI


'''
class UserListView(generic.ListView):
    model = User
    


class ProductListView(generic.ListView):
    model = Product

    def get_context_data(self, **kwargs):
        context = super(ProductListView, self).get_context_data(**kwargs)
        context['category'] = Product.objects.filter(asin=product_ASIN).values('category')[0]['category']
        context['plot'] = plot(product_ASIN)



class ReviewListView(generic.ListView):
    model = Review
    context_object_name = "review_data"

    def get_context_data(self, **kwargs):
        context = super(ReviewView, self).get_context_data(**kwargs)
        context['totalReviews'] = Review.objects.all(asin=product_ASIN).count()
        context['duplicateRatio'] = Product.objects.values('duplicateRatio')
        context['totalDuplicates'] = Review.objects.filter(asin=product_ASIN, duplicate=1).count()
        context['incentivizedRatio'] = Product.objects.values('incentivizedRatio')
        context['totalIncentivized'] = Review.objects.filter(asin=product_ASIN, incentivized=1).count()
        context['reviewAnomalyRatio'] = review_anomaly.detect(product_ASIN)
        context['totalReviewAnomalies'] = review_anomaly.review_anomalies
        context['ratingAnomalyRatio'] = rating_anomaly.detect(product_ASIN)
        context['totalRatingAnomalies'] = rating_anomaly.rating_anomalies
        return context
'''


"""View function for home page of site."""
def index(request):
    # Create a dropdown and text input form instances and populate them with data from the request (binding)
    asin_form = AsinForm(request.GET)

    # when a user types in the search box, autocomplete the first 10 product asin options from their input
    if request.method == 'GET':

        if asin_form.is_valid():
            # redirect to a new URL (result view):
            print("redirecting...")
            return HttpResponseRedirect(reverse('static_result', args=[asin_form.cleaned_data['asin_choice']]))
        
        # autocomplete feature
        if 'asin_id' in request.GET and request.GET['asin_id']:
            products = Product.objects.none()
            if 'category_id' in request.GET and request.GET['category_id'] and request.GET['category_id'] != "(Category)":
                products = Product.objects.filter(asin__istartswith=request.GET['asin_id'], category=request.GET['category_id'])
            else:
                products = Product.objects.filter(asin__istartswith=request.GET['asin_id'])
            
            max_auto_results = 8
            current_count = 0
            titles = []
            # show first eight products that begin with user's input
            for product in products:
                if current_count < max_auto_results:
                    titles.append(product.asin)
                    current_count += 1
                else:
                    break
            return JsonResponse(titles, safe=False)

    else:
        asin_form = AsinForm()

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', {"asin_form": asin_form})
  


'''
    Parameters:
        (productASIN, objects you want to graph...)
'''
def plot(product_ASIN):
    # create a graph
    plt.switch_backend('AGG')
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(ncols=4, figsize=(11, 7))
    fig.subplots_adjust(wspace=0.6)
    
    # plot all axes
    Similarity.plot(ax1)
    Incentivized.plot(ax2)
    ReviewAnomaly.plot(ax3)
    RatingAnomaly.plot(ax4)

    # encode the figure as a png
    buf = BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    image_png = buf.getvalue()
    graph = base64.b64encode(image_png)
    graph = graph.decode('utf-8')
    buf.close()
    return graph



def static_result(request, product_ASIN):
    # Retrieve number of reviews for given product and date range for given product
    reviewsForProduct = Review.objects.filter(asin=product_ASIN).count()
    category = Product.objects.filter(asin=product_ASIN).values('category')[0]['category']

    # Retrieve duplicate review ratio
    incentivizedRatio = Product.objects.values('incentivizedRatio')
    totalIncentivized = Review.objects.filter(asin=product_ASIN, incentivized=1).count()

    # Calculate Review and Rating Anomaly Rate and Interval/range of review posting dates 
    reviewAnomalyRate = review_anomaly.detect(product_ASIN)
    totalReviewAnomalies = review_anomaly.review_anomalies

    ratingAnomalyRate = rating_anomaly.detect(product_ASIN)
    totalRatingAnomalies = rating_anomaly.rating_anomalies

    # Plot graphs for each detection algorithm
    figure = plot(product_ASIN)

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



def search_link(request):
    # Create a dropdown and text input form instances and populate them with data from the request (binding)
    link_form = LinkForm(request.GET)

    # when a user types in the search box, autocomplete the first 10 product asin options from their input
    if request.method == 'POST':
        if link_form.is_valid():
            # remove cache from link
            link = link_form.cleaned_data['link_choice']
            link_keywords = link.split('/')
            asin = link_keywords[link_keywords.index("dp") + 1]

            # redirect to a new URL (result view):
            print("redirecting...")
            return HttpResponseRedirect(reverse('link_result', args=[asin]))

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'search_link.html', {"link_form": link_form})



def link_result(request, product_ASIN):

    # test connection too see if page is valid
    scraper = Scrape()
    if scraper.scrape(asin) == False:
        pass

    # Calculate Duplicate Ratio and number of duplicate reviews
    regression_model = LogisticRegression()
    regression_model.detect(product_ASIN)

    # Calculate Incentivized Ratio and number of incentivized reviews
    sentiment_model

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

    contenxt = {}
    # Render the HTML template index.html with the data in the context variable
    return render(request, 'result.html', context=context)




"""View function for home page of site."""
def about(request):
    context = {
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'about.html', context=context)
