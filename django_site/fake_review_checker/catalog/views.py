# Python Imports
import datetime
import scipy.stats as stats
import matplotlib.pyplot as plt, mpld3
import numpy as np
import pandas as pd

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


# incentivizedReviews = Product.objects.filter(review__asin=productASIN).exclude(incentivizedRatio=0).count()
def result(request, productID):
    # static
    duplicate = Similarity()
    duplicate.calculate(productID)
    duplicateRatio = Product.objects.values('duplicateRatio').filter(asin=productID)[0]['duplicateRatio']

    # Dynamic
    # Calculate Number of Reviews for Given Product
    reviewsForProduct = Review.objects.all().filter(asin=productID).count()

    # Calculate Incentivized Ratio 
    incentivized = Incentivized()
    incentivized.detectKeywords()
    incentivized.calculate(productID)
    incentivizedRatio = Product.objects.values('incentivizedRatio').filter(asin=productID)[0]['incentivizedRatio']

    # Calculate Rating Anomaly Rate and Interval/range of review posting dates 
    r_anomaly = Anomaly()
    r_anomaly.detect(productID)
    ratingAnomalyRate = Product.objects.values('ratingAnomalyRate').filter(asin=productID)[0]['ratingAnomalyRate']
    reviewAnomalyRate = Product.objects.values('reviewAnomalyRate').filter(asin=productID)[0]['reviewAnomalyRate']
    
    # plot fake review score data
    figure = __plot(productID, duplicate, incentivized, r_anomaly)

    # Create html product link
    link = ("https://www.amazon.com/dp/" + productID)

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


    '''
        Parameters:
            (productASIN, objects you want to graph...)
    '''
    def __plot(productASIN, duplicate, incentivized, anomaly):

        # create a graph
        fig, (ax1, ax2, ax3, ax4) = plt.subplots(ncols=4, figsize=(11, 7))
        fig.subplots_adjust(wspace=0.4)



        # Pull duplicate review values ------------------------------------------------------------------------
        duplicateInfo = duplicate.getDuplicateInfo()
        duplicateTimeInts = duplicateInfo["duplicateTimeInts"]
        duplicateScores = duplicateInfo["duplicateScores"]

        # Get duplicate review bins 
        duplicateBins = duplicate.getBins()
        dupTimestamps = [np.datetime64(datetime.datetime.fromtimestamp(x)) for x in duplicateBins]
        del dupTimestamps[-1]

        # Graph Duplicate Reviews
        if (len(duplicateTimeInts) != 0):
            duplicateReviewsCount, bin_edges3, binnumber3 = stats.binned_statistic(duplicateTimeInts, duplicateScores, statistic='count', bins=duplicateBins)
            duplicateReviewsCount = duplicateReviewsCount[np.isfinite(duplicateReviewsCount)]
            duplicateValues = {"timestamp": dupTimestamps, "value": duplicateReviewsCount}
            duplicateSeries = pd.DataFrame(duplicateValues)
            dp = duplicateSeries.plot(x='timestamp', y='value', title='Duplicate Reviews Count', kind='line', ax=ax4)
            dp.set_ylabel("Number of Reviews")
            dp.set_xlabel("Time")
        else:
            fig.delaxes(ax4)



        # Pull incentivized review values ------------------------------------------------------------------------------------
        incentivizedTimesInt = incentivized.getIncentivizedTimes()
        incentivizedScore = incentivized.getIncentivizedScore()

        # Get incentivized review bins 
        incentivizedBins = incentivized.getBins()
        incentivizedTimestamps = [np.datetime64(datetime.datetime.fromtimestamp(x)) for x in incentivizedBins]
        del incentivizedTimestamps[-1]

        # Graph Incentivized Reviews
        if (len(incentivizedTimesInt) != 0):
            incentivizedReviewsCount, bin_edges2, binnumber2 = stats.binned_statistic(incentivizedTimesInt, incentivizedScore, statistic='count', bins=incentivizedTimestamps)
            incentivizedReviewsCount = incentivizedReviewsCount[np.isfinite(incentivizedReviewsCount)]

            incentivizedValues = {"timestamp": incentivizedTimestamps, "value": incentivizedReviewsCount}
            incentivizedSeries = pd.DataFrame(incentivizedValues)
            ip = incentivizedSeries.plot(x='timestamp', y='value', title='Incentivized Reviews Count ', kind='line', ax=ax3, rot=90)
            ip.set_ylabel("Number of Reviews")
            ip.set_xlabel("Time")
        else:
            fig.delaxes(ax3)

        

        # Pull anomaly review values ------------------------------------------------------------------------------------
        series = anomaly.getSeries()
        averageRatingSeries = series["averageRatingSeries"]
        reviewCountsSeries = series["reviewCountsSeries"]

        # Get anomaly review bins 
        anomlyBins = anomaly.getBins()
        anomalybinsTimestamps = [np.datetime64(datetime.datetime.fromtimestamp(x)) for x in anomlyBins]
        anomaly.compressBins()

        # Graph average rating series graph
        rp = averageRatingSeries.plot(x='timestamp', y='value', title='Average Rating', legend = True, kind='line', ax=ax1)
        rp.set_ylabel("Rating Value")
        rp.set_xlabel("Time")



        fig.autofmt_xdate()
        fig_HTML = mpld3.fig_to_html(fig)
        return fig_HTML

