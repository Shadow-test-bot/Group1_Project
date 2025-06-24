# chat/forms.py

from django import forms
from .models import Message
from .models import Group
class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content', 'attachment']
class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name']