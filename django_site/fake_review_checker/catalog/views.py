# Django Imports
from django.shortcuts import render
from django.http import HttpResponse

# Local Imports
from .models import User, Product, Review
from .management.commands.incentivized import Incentivized
from .management.commands.anomaly import ReviewAnomaly

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
    duplicateRatio = Product.objects.values('duplicateRatio').filter(asin=productID)[0]['duplicateRatio']

    # Dynamic
    # Calculate Incentivized Ratio 
    incentivized = Incentivized()
    incentivized.detectKeywords()
    incentivizedList = incentivized.calculate(productID)
    incentivizedRatio = Product.objects.values('incentivizedRatio').filter(asin=productID)[0]['incentivizedRatio']

    incentivizedTimesInt = incentivizedList[0]
    incentivizedScore = incentivizedList[1]

    # Calculate Rating Anomaly Rate and Interval/range of review posting dates 
    r_anomaly = ReviewAnomaly()
    r_anomaly = detect(productID)
    ratingAnomalyRate = Product.objects.values('ratingAnomalyRate').filter(asin=productID)[0]['ratingAnomalyRate']
    reviewRange = r_anomaly.getDateRange()

    # Calculate Review Anomaly Rate
    reviewAnomalyRate = Product.objects.values('reviewAnomalyRate').filter(asin=productID)[0]['reviewAnomalyRate']
    
    # Calculate Number of Reviews for Given Product
    reviewsForProduct = Review.objects.all().filter(asin=productID).count()

    # Create html product link
    link = ("https://www.amazon.com/dp/" + productID)

    context = {
        'duplicateRatio': duplicateRatio,
        'incentivizedRatio': incentivizedRatio,
        'ratingAnomalyRate': ratingAnomalyRate,
        'reviewAnomalyRate': reviewAnomalyRate,
        'reviewRange': reviewRange,
        'reviewsForProduct': reviewsForProduct,
        'link': link,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'result.html', context=context)


    '''
    def plot():
        # get posting date range (earliest post - most recent post)
        mostRecentDate = Review.objects.filter(asin=productASIN).aggregate(Min('unixReviewTime'))
        farthestDate = Review.objects.filter(asin=productASIN).aggregate(Max('unixReviewTime'))
        reviewRange = datetime.datetime.fromtimestamp(farthestDate['unixReviewTime__max']) - datetime.datetime.fromtimestamp(mostRecentDate['unixReviewTime__min'])

        # save review range
        self.reviewDayRange = reviewRange.days
        self.bucketCount = reviewRange.days / 30
        print("It has reviews ranging " + str(self.reviewDayRange) + " days. Bucket count " + str(self.bucketCount))

        # Returns num evenly spaced samples, calculated over the interval [start, stop]. num = Number of samples to generate
        bins = np.linspace(mostRecentDate['unixReviewTime__min'], farthestDate['unixReviewTime__max'], int(self.reviewDayRange) + 2)
        
        # Calculate sets of review anomaly data for histogram bins
        reviews = Review.objects.filter(asin=productASIN)
        reviewTimes = [datetime.datetime.fromtimestamp(review['unixReviewTime']).strftime("%m/%d/%Y") for review in reviews.values('unixReviewTime').order_by('unixReviewTime')]
        reviewTimesInt = [review['unixReviewTime'] for review in reviews.values('unixReviewTime').order_by('unixReviewTime')]
        reviewScores = [review['overall'] for review in reviews.values('overall').order_by('overall')]

        # Calculate sets of incentivized review data for histogram bins
        incentivized = Incentivized()
        incentivized.detectKeywords()
        incentivizedList = incentivized.calculate(productASIN)
        incentivizedTimesInt = incentivizedList[0]
        incentivizedScore = incentivizedList[1]

        # function computes the mean binned statistical value for the given data (similar to histogram function)
        averageRating, bin_edges, binnumber = stats.binned_statistic(reviewTimesInt, reviewScores, statistic='mean', bins=bins)
        averageRating = averageRating[np.isfinite(averageRating)]

        # function computes the count of the given data (similar to histogram function)
        reviewsCount, bin_edges1, binnumber1 = stats.binned_statistic(reviewTimesInt, reviewScores, statistic='count', bins=bins)
        reviewsCount = reviewsCount[np.isfinite(reviewsCount)]

        binsTimestamps = [np.datetime64(datetime.datetime.fromtimestamp(x)) for x in bins]
        incentivizedBinTimestamps = [x for x in binsTimestamps]
        del incentivizedBinTimestamps[-1]

        i = j = 0
        n = len(reviewsCount)
        # print (str(len(binsTimestamps)) + " " + str(n))
        while i < n:
            if reviewsCount[i] == 0:
                del binsTimestamps[j]
                i = i + 1
            else:
                j = j + 1
                i = i + 1
        del binsTimestamps[-1]
        reviewsCount = reviewsCount[reviewsCount != 0]

        # make a review count data frame
        plot_data = {'Average Rating': averageRating, 'Count': reviewsCount}
        review_series = pd.DataFrame(plot_data)

        # make a time series data frame
        averageRatingValues = {"timestamp": binsTimestamps, "value": averageRating}
        averageRatingSeries = pd.DataFrame(averageRatingValues)


        fig, (ax1, ax2, ax3, ax4) = plt.subplots(ncols=4, figsize=(11, 7))
        fig.subplots_adjust(wspace=0.4)
        
        rp = averageRatingSeries.plot(x='timestamp', y='value', title='Average Rating', legend = True, kind='line', ax=ax1)
        rp.set_ylabel("Rating Value")
        rp.set_xlabel("Time")

        ratingValueAnamolies = defaultdict(dict)
        try:
            ratingValueAnamolies = detect_ts(averageRatingSeries, max_anoms=0.02, direction='both')
        except:
            ratingValueAnamolies['anoms']['anoms'] = []


        if (len(incentivizedTimesInt) != 0):
            incentivizedReviewsCount, bin_edges2, binnumber2 = stats.binned_statistic(
                incentivizedTimesInt, incentivizedScore, statistic='count', bins=bins)
            incentivizedReviewsCount = incentivizedReviewsCount[np.isfinite(incentivizedReviewsCount)]

            print(len(incentivizedBinTimestamps))
            print(len(incentivizedReviewsCount))
            incentivizedValues = {"timestamp": incentivizedBinTimestamps, "value": incentivizedReviewsCount}
            incentivizedSeries = pd.DataFrame(incentivizedValues)
            ip = incentivizedSeries.plot(x='timestamp', y='value', title='Incentivized Reviews Count ',
                                kind='line', ax=ax3, rot=90)
            ip.set_ylabel("Number of Reviews")
            ip.set_xlabel("Time")
        else:
            fig.delaxes(ax3)


        if (len(reviewTimesInt) != 0):
            duplicateReviewsCount, bin_edges3, binnumber3 = stats.binned_statistic(
                reviewTimesInt, reviewScores, statistic='count', bins=bins)
            duplicateReviewsCount = duplicateReviewsCount[np.isfinite(duplicateReviewsCount)]

            print(len(incentivizedBinTimestamps))
            print(len(duplicateReviewsCount))
            duplicateValues = {"timestamp": incentivizedBinTimestamps, "value": duplicateReviewsCount}
            duplicateSeries = pd.DataFrame(duplicateValues)
            dp = duplicateSeries.plot(x='timestamp', y='value', title='Duplicate Reviews Count',
                                kind='line', ax=ax4)
            dp.set_ylabel("Number of Reviews")
            dp.set_xlabel("Time")
        else:
            fig.delaxes(ax4)
    '''