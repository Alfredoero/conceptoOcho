from django import forms

class PostForm(forms.Form):
	do_search = forms.CharField(label='Search', max_length=200)