from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django_countries.fields import CountryField

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, blank=True)
    country = CountryField(blank=True, null=True)
    height = models.FloatField(null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    ACTIVITY_CHOICES = [
        ('sedentary', 'Sedentary'),
        ('lightly_active', 'Lightly Active'),
        ('moderately_active', 'Moderately Active'),
        ('very_active', 'Very Active'),
        ('extra_active', 'Extra Active'),
    ]
    activity_level = models.CharField(max_length=20, choices=ACTIVITY_CHOICES, null=True, blank=True)
    WEIGHT_GOAL_CHOICES = [
        ('lose', 'Lose Weight'),
        ('maintain', 'Maintain Weight'),
        ('gain', 'Gain Weight'),
    ]
    weight_goal = models.CharField(max_length=10, choices=WEIGHT_GOAL_CHOICES, null=True, blank=True)
    known_allergies = models.TextField(blank=True)
    dietary_preferences = models.TextField(blank=True)
    health_conditions = models.TextField(blank=True)
    daily_calorie_goal = models.IntegerField(null=True, blank=True)
    daily_protein_goal = models.IntegerField(null=True, blank=True)
    daily_carbs_goal = models.IntegerField(null=True, blank=True)
    daily_fat_goal = models.IntegerField(null=True, blank=True)
    blood_pressure_systolic = models.IntegerField(null=True, blank=True)
    blood_pressure_diastolic = models.IntegerField(null=True, blank=True)
    blood_sugar = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.user.username

class HealthMetricLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    weight = models.FloatField(null=True, blank=True)
    blood_pressure_systolic = models.IntegerField(null=True, blank=True)
    blood_pressure_diastolic = models.IntegerField(null=True, blank=True)
    blood_sugar = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ['user', 'date']

class NutritionalValue(models.Model):
    calories = models.IntegerField(default=0)
    protein = models.FloatField(default=0)
    carbs = models.FloatField(default=0)
    fat = models.FloatField(default=0)
    fiber = models.FloatField(default=0)
    sugar = models.FloatField(default=0)
    sodium = models.FloatField(default=0)
    cholesterol = models.FloatField(default=0)
    saturated_fat = models.FloatField(default=0)
    unsaturated_fat = models.FloatField(default=0)
    trans_fat = models.FloatField(default=0)
    vitamin_a = models.FloatField(default=0)
    vitamin_c = models.FloatField(default=0)
    calcium = models.FloatField(default=0)
    iron = models.FloatField(default=0)

    def __str__(self):
        return f"Nutritional Value for {self.meal_data}"

class MealType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Meal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    date_time = models.DateTimeField()
    meal_type = models.ForeignKey(MealType, on_delete=models.SET_NULL, null=True)
    ingredients = models.TextField()
    portion_size = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    nutritional_insights = models.TextField(blank=True)
    nutritional_value = models.OneToOneField(NutritionalValue, on_delete=models.SET_NULL, null=True, blank=True, related_name='meal_data')

    def __str__(self):
        return f"{self.name} - {self.date_time.strftime('%Y-%m-%d %H:%M:%S')}"

class Symptom(models.Model):
    SEVERITY_CHOICES = [
        ('Mild', 'Mild'),
        ('Moderate', 'Moderate'),
        ('Severe', 'Severe'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date_time = models.DateTimeField(default=timezone.now)
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)

    def __str__(self):
        return f"{self.date_time.strftime('%Y-%m-%d %H:%M:%S')} - {self.description[:50]}"

class FoodItem(models.Model):
    name = models.CharField(max_length=100)
    calories = models.IntegerField()
    protein = models.FloatField()
    carbs = models.FloatField()
    fat = models.FloatField()
    fiber = models.FloatField(default=0)
    sugar = models.FloatField(default=0)
    sodium = models.FloatField(default=0)
    cholesterol = models.FloatField(default=0)
    saturated_fat = models.FloatField(default=0)
    unsaturated_fat = models.FloatField(default=0)
    trans_fat = models.FloatField(default=0)
    vitamin_a = models.FloatField(default=0)
    vitamin_c = models.FloatField(default=0)
    calcium = models.FloatField(default=0)
    iron = models.FloatField(default=0)
    recommended_for = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name

class FoodRecommendation(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='food_recommendations')
    recommendation = models.CharField(max_length=200)
    description = models.TextField()
    image_url = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_profile.user.username} - {self.recommendation}"

class DietPlan(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    plan_date = models.DateField()
    meals = models.JSONField()  
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Diet Plan for {self.user_profile.user.username} on {self.plan_date}"

class Achievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50)
    date_earned = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.name}"

class UserStreak(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='streak')
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_log_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Streak"

class CountryMeal(models.Model):
    name = models.CharField(max_length=100)
    country = CountryField()
    ingredients = models.TextField()
    is_ai_generated = models.BooleanField(default=True)
    times_selected = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name} ({self.country.name})"