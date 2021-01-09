from datetime import datetime

from django.conf import settings
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from django.forms import DateInput

from .models import Player, Event


class PlayerCreationForm(UserCreationForm):
    class Meta:
        model = Player
        fields = ['email', 'first_name', 'last_name', 'gender', 'date_of_birth']
        widgets = {
            'date_of_birth': DateInput(format=settings.DATE_FORMAT, attrs={'type': 'date'}),
        }


class PlayerChangeForm(UserChangeForm):
    class Meta:
        model = Player
        fields = ['first_name', 'last_name', 'gender', 'date_of_birth', 'mobile_number']
        widgets = {
            'date_of_birth': DateInput(format=settings.TIME_FORMAT, attrs={'type': 'date'}),
        }


class EventCreateForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['court', 'court_detail', 'play_date', 'play_start_time', 'player_quota', 'play_detail']
        widgets = {
            'play_date': DateInput(format=settings.DATE_FORMAT, attrs={'type': 'date', 'value': datetime.today().strftime(settings.DATE_FORMAT)},),
            'play_start_time': DateInput(format=settings.TIME_FORMAT, attrs={'type': 'time', 'value': datetime.now().strftime(settings.TIME_FORMAT)},),
        }


class GroupEventCreateForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['court', 'court_detail', 'play_date', 'play_start_time', 'player_quota', 'is_public', 'play_detail']
        widgets = {
            'play_date': DateInput(format=settings.DATE_FORMAT, attrs={'type': 'date', 'value': datetime.today().strftime(settings.DATE_FORMAT)},),
            'play_start_time': DateInput(format=settings.TIME_FORMAT, attrs={'type': 'time', 'value': datetime.now().strftime(settings.TIME_FORMAT)},),
        }
