# Django Imports
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

# Local Imports
from .models import User, Product, Review



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
    link_choice = forms.CharField(label="", max_length=30, required=True)

    def clean_asin_choice(self):
        # get the cleaned version of the field data, and return it regardless if it is changed
        data = self.cleaned_data['link_choice']

        # if the choice is not a valid asin, display an error text to the screen with ValidationError
        if 'amazon' not in data or data == None or data == '':
            raise ValidationError(_("'" + str(data) + "' is not a valid link"))
        # have a check to check if page is valid

        return data

    class Meta:
        category = ""
    
    


