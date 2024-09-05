from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Meal, Symptom, UserProfile, MealType, CountryMeal, HealthMetricLog
from django.forms.widgets import DateTimeInput
from django.utils import timezone
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget
from django.db.models import Max

class CustomDateTimeInput(DateTimeInput):
    input_type = 'datetime-local'

class CustomSymptomDateTimeInput(DateTimeInput):
    input_type = 'text'
    
    def format_value(self, value):
        return value.strftime('%Y-%m-%d-%H:%M') if value else ''

class CustomUserCreationForm(UserCreationForm):
    full_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'placeholder': 'Full Name'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'Email'}))
    phone_number = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'placeholder': 'Phone Number'}))

    class Meta:
        model = User
        fields = ('username', 'full_name', 'email', 'phone_number', 'password1', 'password2')

    def save(self, commit=True):
        user = super(CustomUserCreationForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                full_name=self.cleaned_data['full_name'],
                phone_number=self.cleaned_data['phone_number']
            )
        return user

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label='Username or Email', widget=forms.TextInput(attrs={'placeholder': 'Username or Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone_number', 'country', 'height', 'age', 'gender', 'activity_level', 'weight_goal', 'known_allergies', 'dietary_preferences', 'health_conditions', 'daily_calorie_goal', 'daily_protein_goal', 'daily_carbs_goal', 'daily_fat_goal']
        widgets = {
            'country': CountrySelectWidget(),
        }

class MealForm(forms.ModelForm):
    existing_meal = forms.ModelChoiceField(
        queryset=Meal.objects.all(),
        required=False,
        empty_label="Select an existing meal (optional)"
    )
    date_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'class': 'datetimepicker'}),
        input_formats=['%Y-%m-%d %H:%M']
    )
    meal_type = forms.ModelChoiceField(queryset=MealType.objects.all(), required=False)

    class Meta:
        model = Meal
        fields = ['name', 'date_time', 'meal_type', 'ingredients', 'portion_size', 'notes']
        widgets = {
            'date_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(MealForm, self).__init__(*args, **kwargs)
        if self.user:
            # Get the latest meal for each unique name
            latest_meals = Meal.objects.filter(user=self.user).values('name').annotate(
                latest_id=Max('id')
            ).values('latest_id')
            meals = Meal.objects.filter(id__in=latest_meals).order_by('name')
            self.fields['existing_meal'].queryset = meals
            self.fields['existing_meal'].label_from_instance = lambda obj: obj.name
        self.fields['meal_type'].queryset = MealType.objects.all()

    def save(self, commit=True):
        meal = super().save(commit=False)
        if self.user:
            meal.user = self.user
        if commit:
            meal.save()
        return meal

class SymptomForm(forms.ModelForm):
    date_time = forms.DateTimeField(
        widget=CustomSymptomDateTimeInput(format='%Y-%m-%d-%H:%M'),
        input_formats=['%Y-%m-%d-%H:%M'],
        initial=timezone.now
    )

    class Meta:
        model = Symptom
        fields = ['date_time', 'description', 'severity']

class HealthMetricForm(forms.ModelForm):
    class Meta:
        model = HealthMetricLog
        fields = ['weight', 'blood_pressure_systolic', 'blood_pressure_diastolic', 'blood_sugar']
        widgets = {
            'weight': forms.NumberInput(attrs={'step': '0.1'}),
            'blood_pressure_systolic': forms.NumberInput(attrs={'step': '1'}),
            'blood_pressure_diastolic': forms.NumberInput(attrs={'step': '1'}),
            'blood_sugar': forms.NumberInput(attrs={'step': '0.1'}),
        }

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
