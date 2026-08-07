#forms.py
from django import forms
from .models import Message

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content', 'file']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'پیام خود را بنویسید...'}),
        }
    content = forms.CharField(
        label='',
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder': 'پیام خود را بنویسید...'
        })
    )
