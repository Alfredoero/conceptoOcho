from django import forms

class PostForm(forms.Form):
	do_search = forms.CharField(label='Search', max_length=200)
	#num_results = forms.CharField(label='Result Number', max_length=20)
	search_city = forms.CharField(label='City', max_length=200)
	search_country = forms.CharField(label='Country', max_length=150)