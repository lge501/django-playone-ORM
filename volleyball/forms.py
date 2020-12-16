from datetime import datetime

from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from django.forms import DateInput

from .models import Player, Event


class PlayerCreationForm(UserCreationForm):
    class Meta:
        model = Player
        fields = ['email', 'first_name', 'last_name', 'gender', 'date_of_birth']


class PlayerChangeForm(UserChangeForm):
    class Meta:
        model = Player
        fields = ['first_name', 'last_name', 'gender', 'date_of_birth', 'mobile_number']


class EventCreateForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['court', 'court_detail', 'play_date', 'play_start_time', 'player_quota', 'play_detail']
        widgets = {
            'play_date': DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'value': datetime.today().strftime('%Y-%m-%d')},),
            'play_start_time': DateInput(format='%H:%M', attrs={'type': 'time', 'value': datetime.now().strftime('%H:%M')},),
        }
