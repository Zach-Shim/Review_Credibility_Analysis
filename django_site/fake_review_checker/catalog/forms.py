# Python Imports
from bs4 import BeautifulSoup
import requests

# Django Imports
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

# Local Imports
from .models import User, Product, Review
from .management.commands.scrape import Scrape



class AsinForm(forms.Form):
    category_choice = forms.ModelChoiceField(label="", queryset=Product.objects.values_list('category', flat=True).distinct(), required=False, to_field_name='category', empty_label="(Category)")
    asin_choice = forms.CharField(label="", max_length=30, required=True, widget=forms.TextInput(attrs={'placeholder': 'Enter an asin'}))

    def clean_asin_choice(self):
        # get the cleaned version of the field data, and return it regardless if it is changed
        data = self.cleaned_data['asin_choice']

        # if the choice is not a valid asin, display an error text to the screen with ValidationError
        asin = Product.objects.filter(asin__iexact=data)
        if not asin or data == None or data == '':
            raise ValidationError(_("'" + str(data) + "' is not a valid asin"))

        return data



class LinkForm(forms.Form):
    link_choice = forms.CharField(label="", required=True, widget=forms.TextInput(attrs={'placeholder': 'Enter an Amazon link'}))

    def clean_link_choice(self):
        # get the cleaned version of the field data, and return it regardless if it is changed
        link = self.cleaned_data['link_choice']
        
        # if the choice is not a valid asin, display an error text to the screen with ValidationError
        if 'amazon' not in link or link == None or link == '':
            raise ValidationError(_("Invalid link"))

        try:
            # remove cache from link
            link_keywords = link.split('/')
            asin = link_keywords[link_keywords.index("dp") + 1]
            link = "http://www.amazon.com/dp/" + asin
        except:
            raise ValidationError(_("Invalid link"))

        # test connection too see if page is valid
        scraper = Scrape()
        if scraper.test_connection(asin) == False:
            raise ValidationError(_(scraper.get_error()))
        
        return link