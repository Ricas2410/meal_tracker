import csv
import json
import random
from collections import defaultdict
from datetime import datetime, timedelta
import spacy
from django.db.models import Avg, Count
from django.http import HttpResponse
from django.utils import timezone

from .models import Meal, Symptom, UserProfile, FoodItem, FoodRecommendation, CountryMeal

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# CSV Export
def export_as_csv(queryset, fields, filename):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
    writer = csv.writer(response)
    writer.writerow(fields)
    for obj in queryset:
        writer.writerow([getattr(obj, field) for field in fields])
    return response

# Meal Generation
def generate_country_meals(country, num_meals=10):
    meal_types = ["Breakfast", "Lunch", "Dinner", "Snack", "Dessert"]
    cooking_methods = ["Fried", "Baked", "Grilled", "Boiled", "Steamed", "Roasted"]
    common_ingredients = ["Rice", "Chicken", "Beef", "Fish", "Vegetables", "Fruits", "Bread", "Pasta", "Potatoes"]

    country_doc = nlp(country)
    meals = []
    for _ in range(num_meals):
        meal_type = random.choice(meal_types)
        cooking_method = random.choice(cooking_methods)
        main_ingredient = random.choice(common_ingredients)
        meal_name = f"{country}'s {cooking_method} {main_ingredient} {meal_type}"
        ingredients = random.sample(common_ingredients, k=random.randint(3, 6))
        meals.append({"name": meal_name, "ingredients": ingredients})
    return meals

# Warning Generation
def generate_warnings(user):
    meal_logs = Meal.objects.filter(user=user)
    symptom_logs = Symptom.objects.filter(user=user)
    return [
        f"Potential issue with {meal.ingredients} on {meal.date_time.date()}"
        for meal in meal_logs
        for symptom in symptom_logs
        if symptom.date_time.date() == meal.date_time.date()
        and symptom.description in meal.ingredients
    ]

def suggest_food_limitations(user):
    symptom_logs = Symptom.objects.filter(user=user)
    food_limitations = defaultdict(int)
    for symptom in symptom_logs:
        meal_logs = Meal.objects.filter(user=user, date_time__date=symptom.date_time.date())
        for meal in meal_logs:
            for item in meal.ingredients.split(', '):
                food_limitations[item] += 1
    return [item for item, count in food_limitations.items() if count > 2]

def check_for_diet_warnings(user):
    warnings = []
    user_profile = user.userprofile
    known_allergies = user_profile.known_allergies.split(', ')
    health_conditions = user_profile.health_conditions.split(', ')
    recent_meals = Meal.objects.filter(user=user).order_by('-date_time')[:10]
    for meal in recent_meals:
        warnings.extend([
            f"Warning: Your recent meal contains {allergy}, which you're allergic to."
            for allergy in known_allergies
            if allergy.lower() in meal.ingredients.lower()
        ])
        warnings.extend([
            "Warning: This meal contains sugar, which might not be suitable for diabetes."
            for condition in health_conditions
            if condition.lower() == 'diabetes' and 'sugar' in meal.ingredients.lower()
        ])
    return warnings

# Diet Plan Generation
def generate_diet_plan(user_profile, start_date, days=7):
    allergies = set(user_profile.known_allergies.lower().split(', '))
    health_conditions = set(user_profile.health_conditions.lower().split(', '))
    preferences = user_profile.dietary_preferences.lower()

    suitable_foods = FoodItem.objects.exclude(name__in=allergies)
    if 'vegetarian' in preferences:
        suitable_foods = suitable_foods.filter(recommended_for__icontains='vegetarian')
    elif 'vegan' in preferences:
        suitable_foods = suitable_foods.filter(recommended_for__icontains='vegan')

    if 'diabetes' in health_conditions:
        suitable_foods = suitable_foods.filter(carbs__lte=30)
    if 'hypertension' in health_conditions:
        suitable_foods = suitable_foods.filter(recommended_for__icontains='low sodium')

    base_calories = 2000 if user_profile.user.userprofile.gender == 'Male' else 1800
    daily_calories = base_calories * 1.2  # Assuming sedentary activity level

    plan = {}
    for day in range(days):
        date = start_date + timedelta(days=day)
        daily_plan = {meal: [] for meal in ["breakfast", "lunch", "dinner", "snacks"]}
        meal_calories = {
            "breakfast": daily_calories * 0.25,
            "lunch": daily_calories * 0.35,
            "dinner": daily_calories * 0.30,
            "snacks": daily_calories * 0.10
        }

        for meal, calories in meal_calories.items():
            remaining_calories = calories
            while remaining_calories > 50:
                food = random.choice(suitable_foods.filter(calories__lte=remaining_calories))
                daily_plan[meal].append(food.name)
                remaining_calories -= food.calories

        plan[date] = daily_plan

    return plan

# Trend Analysis
def analyze_meal_symptom_trends(user, days=30):
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    meals = Meal.objects.filter(user=user, date_time__range=[start_date, end_date])
    symptoms = Symptom.objects.filter(user=user, date_time__range=[start_date, end_date])

    meal_counts = meals.values('meal_type').annotate(count=Count('id'))
    common_ingredients = analyze_common_ingredients(meals)
    symptom_counts = symptoms.values('description').annotate(count=Count('id'))
    symptom_severity = symptoms.values('severity').annotate(count=Count('id'))
    correlations = analyze_meal_symptom_correlation(meals, symptoms)

    return {
        'meal_counts': meal_counts,
        'common_ingredients': common_ingredients,
        'symptom_counts': symptom_counts,
        'symptom_severity': symptom_severity,
        'correlations': correlations,
        'total_meals': meals.count(),
        'total_symptoms': symptoms.count(),
        'date_range': {'start': start_date, 'end': end_date}
    }

def analyze_common_ingredients(meals, top_n=5):
    ingredient_counts = defaultdict(int)
    for meal in meals:
        for ingredient in meal.ingredients.split(', '):
            ingredient_counts[ingredient.lower().strip()] += 1
    return sorted(ingredient_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]

def analyze_meal_symptom_correlation(meals, symptoms):
    correlations = defaultdict(lambda: defaultdict(int))
    for symptom in symptoms:
        related_meals = meals.filter(date_time__date=symptom.date_time.date())
        for meal in related_meals:
            for ingredient in meal.ingredients.split(', '):
                correlations[symptom.description][ingredient.lower().strip()] += 1

    return {
        symptom: dict(sorted(ingredients.items(), key=lambda x: x[1], reverse=True)[:3])
        for symptom, ingredients in correlations.items()
        if any(count > 1 for count in ingredients.values())
    }

# Food Recommendations
def generate_food_recommendations(user_profile):
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    meals = Meal.objects.filter(user=user_profile.user, date_time__range=[start_date, end_date])
    symptoms = Symptom.objects.filter(user=user_profile.user, date_time__range=[start_date, end_date])

    nutrient_intake = analyze_nutrient_intake(meals)
    food_symptom_correlation = analyze_food_symptom_correlation(meals, symptoms)

    recommendations = []
    for nutrient, intake in nutrient_intake.items():
        if intake['average'] < intake['recommended'] * 0.7:
            recommendations.append((
                f"Consider increasing {nutrient} intake",
                f"Your average {nutrient} intake is lower than recommended. Try incorporating more {nutrient}-rich foods in your diet."
            ))
        elif intake['average'] > intake['recommended'] * 1.3:
            recommendations.append((
                f"Consider moderating {nutrient} intake",
                f"Your average {nutrient} intake is higher than recommended. Try to balance your diet with a variety of foods."
            ))

    recommendations.extend(
        (f"Consider monitoring your reaction to {food}",
         f"Our analysis suggests a potential sensitivity to {food}. Consider keeping a detailed food diary and consulting with a healthcare professional.")
        for food, data in food_symptom_correlation.items()
        if data['correlation'] > 0.7 and data['occurrences'] > 5
    )

    if len(recommendations) < 3:
        recommendations.append((
            "Maintain a balanced diet",
            "Continue to eat a variety of fruits, vegetables, whole grains, lean proteins, and healthy fats to support overall health."
        ))

    FoodRecommendation.objects.filter(user_profile=user_profile).delete()
    for recommendation, description in recommendations:
        FoodRecommendation.objects.create(
            user_profile=user_profile,
            recommendation=recommendation,
            description=description,
            image_url=recommendation.get('image_url', '')  # Add this line
        )

    return recommendations

def analyze_nutrient_intake(meals):
    nutrient_intake = defaultdict(lambda: {'total': 0, 'count': 0})
    for meal in meals:
        ingredients = meal.ingredients.split(', ')
        for ingredient in ingredients:
            if food_item := FoodItem.objects.filter(name__iexact=ingredient).first():
                for nutrient in ['calories', 'fat', 'protein', 'carbs']:
                    nutrient_intake[nutrient]['total'] += getattr(food_item, nutrient)
                    nutrient_intake[nutrient]['count'] += 1

    recommended_values = {'calories': 2000, 'fat': 65, 'protein': 50, 'carbs': 300}
    for nutrient, data in nutrient_intake.items():
        data['average'] = data['total'] / data['count'] if data['count'] > 0 else 0
        data['recommended'] = recommended_values.get(nutrient, 0)

    return nutrient_intake

def analyze_food_symptom_correlation(meals, symptoms):
    food_symptom_correlation = defaultdict(lambda: {'symptom_count': 0, 'occurrences': 0})
    for meal in meals:
        ingredients = meal.ingredients.split(', ')
        related_symptoms = symptoms.filter(date_time__gt=meal.date_time, date_time__lt=meal.date_time + timedelta(hours=4))
        for ingredient in ingredients:
            food_symptom_correlation[ingredient]['occurrences'] += 1
            food_symptom_correlation[ingredient]['symptom_count'] += related_symptoms.count()

    for data in food_symptom_correlation.values():
        data['correlation'] = data['symptom_count'] / data['occurrences'] if data['occurrences'] > 0 else 0

    return food_symptom_correlation

def analyze_meal_description(description):
    doc = nlp(description)
    return [ent.text for ent in doc.ents if ent.label_ in ["FOOD", "INGREDIENT"]]

# This function is a placeholder and needs to be implemented with a proper nutrition API
def fetch_nutritional_data(ingredients):
    # Implement API call to a nutrition database here
    pass

def get_country_from_ip(ip_address):
    # Placeholder function
    # In a real implementation, you would use a geolocation service or database
    return None

