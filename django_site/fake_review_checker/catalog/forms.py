# Django Imports
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

# Local Imports
from .models import User, Product, Review



class AsinForm(forms.Form):
    asin_choice = forms.CharField(label="Asin Choice", max_length=30, required=True, help_text="Enter a product asin you would like to search")

    def clean_asin_choice(self):
        data = self.cleaned_data['asin_choice']

        asin = Product.objects.filter(asin__iexact=data)
        if not asin or data == None:
            raise ValidationError(_('Invalid Asin - Product has not been analyzed yet'))

        return data


