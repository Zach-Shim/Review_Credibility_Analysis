# Django Imports
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

# Local Imports
from .models import User, Product, Review



class AsinForm(forms.Form):
    asin_choice = forms.CharField(label="Asin Choice", max_length=30, required=True, help_text="Enter a product asin you would like to search")


    class Meta:
        category = ""



    def clean_asin_choice(self):
        # get the cleaned version of the field data, and return it regardless if it is changed
        data = self.cleaned_data['asin_choice']

        # if the choice is not a valid asin, display an error text to the screen with ValidationError
        asin = Product.objects.filter(asin__iexact=data)
        if not asin or data == None or data == '':
            raise ValidationError(_('Invalid Asin - Product has not been analyzed yet'))

        return data


