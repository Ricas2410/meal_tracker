# tracker/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .forms import MealForm, SymptomForm,  CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm, HealthMetricForm, UserForm
from django.shortcuts import render
from .models import Meal, Symptom, UserProfile, FoodRecommendation, DietPlan, Achievement, UserStreak, FoodItem, MealType, CountryMeal, HealthMetricLog, NutritionalValue
from django.http import HttpResponse, JsonResponse
from .utils import export_as_csv, generate_warnings, suggest_food_limitations, generate_diet_plan, analyze_meal_symptom_trends, generate_food_recommendations, analyze_meal_description, fetch_nutritional_data
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import datetime, timedelta
from django.contrib import messages
from django.db.models import Count
from django.db.models.functions import TruncDate
import json
from django.db.models import Avg, Max, Min
import random
import requests
from django_countries import countries
from .ai_utils import generate_country_meals
from .nutritionix_api import get_nutritional_info
from .health_advice import generate_health_advice
from django.db.models import Sum

@login_required
def data_summary(request):
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)  # Last 30 days

    meals = Meal.objects.filter(user=request.user, date_time__date__range=[start_date, end_date])
    symptoms = Symptom.objects.filter(user=request.user, date_time__date__range=[start_date, end_date])

    meal_summary = {
        'total': meals.count(),
        'avg_per_day': meals.count() / 30,
        'most_common_type': meals.values('meal_type').annotate(count=Count('meal_type')).order_by('-count').first()
    }

    symptom_summary = {
        'total': symptoms.count(),
        'avg_per_day': symptoms.count() / 30,
        'avg_severity': symptoms.aggregate(Avg('severity'))['severity__avg'] or 0,
        'most_common': symptoms.values('description').annotate(count=Count('description')).order_by('-count').first()
    }

    # Meal type distribution
    meal_types = list(meals.values_list('meal_type', flat=True).distinct())
    meal_type_counts = [meals.filter(meal_type=mt).count() for mt in meal_types]

    # Symptom frequency
    symptom_data = symptoms.values('description').annotate(count=Count('description')).order_by('-count')[:5]
    symptom_labels = [item['description'] for item in symptom_data]
    symptom_counts = [item['count'] for item in symptom_data]

    # Nutritional data over time
    nutrition_data = meals.values('date_time__date').annotate(
        calories=Avg('nutritional_value__calories'),
        protein=Avg('nutritional_value__protein'),
        carbs=Avg('nutritional_value__carbs'),
        fat=Avg('nutritional_value__fat')
    ).order_by('date_time__date')

    nutrition_dates = [item['date_time__date'].strftime('%Y-%m-%d') for item in nutrition_data]
    calorie_data = [item['calories'] for item in nutrition_data]
    protein_data = [item['protein'] for item in nutrition_data]
    carb_data = [item['carbs'] for item in nutrition_data]
    fat_data = [item['fat'] for item in nutrition_data]

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'meal_summary': meal_summary,
        'symptom_summary': symptom_summary,
        'meal_types': json.dumps(meal_types),
        'meal_type_counts': json.dumps(meal_type_counts),
        'symptom_labels': json.dumps(symptom_labels),
        'symptom_counts': json.dumps(symptom_counts),
        'nutrition_dates': json.dumps(nutrition_dates),
        'calorie_data': json.dumps(calorie_data),
        'protein_data': json.dumps(protein_data),
        'carb_data': json.dumps(carb_data),
        'fat_data': json.dumps(fat_data),
    }

    return render(request, 'tracker/data_summary.html', context)

def get_meal_summary(current_meals, previous_meals, date_diff):
    current_count = current_meals.count()
    previous_count = previous_meals.count()
    avg_per_day = current_count / date_diff
    prev_avg_per_day = previous_count / date_diff
    trend = ((avg_per_day - prev_avg_per_day) / prev_avg_per_day) * 100 if prev_avg_per_day > 0 else 0

    return {
        'total': current_count,
        'avg_per_day': avg_per_day,
        'most_common_type': current_meals.values('meal_type').annotate(count=Count('id')).order_by('-count').first(),
        'trend': trend,
    }

def get_symptom_summary(current_symptoms, previous_symptoms, date_diff):
    current_count = current_symptoms.count()
    previous_count = previous_symptoms.count()
    avg_per_day = current_count / date_diff
    prev_avg_per_day = previous_count / date_diff
    trend = ((avg_per_day - prev_avg_per_day) / prev_avg_per_day) * 100 if prev_avg_per_day > 0 else 0

    return {
        'total': current_count,
        'avg_per_day': avg_per_day,
        'avg_severity': current_symptoms.aggregate(Avg('severity'))['severity__avg'] or 0,
        'most_common': current_symptoms.values('description').annotate(count=Count('id')).order_by('-count').first(),
        'trend': trend,
    }

def get_insights(meals, symptoms):
    insights = []
    if meals.exists() and symptoms.exists():
        common_meal = meals.values('meal_type').annotate(count=Count('id')).order_by('-count').first()
        common_symptom = symptoms.values('description').annotate(count=Count('id')).order_by('-count').first()
        insights.append(f"Your most common meal type is {common_meal['meal_type']} and your most frequent symptom is {common_symptom['description']}.")
    return insights

def get_recommendations(meal_summary, symptom_summary):
    recommendations = []
    if meal_summary['trend'] > 10 and symptom_summary['trend'] > 10:
        recommendations.append("Consider reducing your meal frequency slightly, as both meal and symptom frequencies have increased.")
    elif symptom_summary['avg_severity'] > 7:
        recommendations.append("Your average symptom severity is high. Consider consulting with a healthcare professional.")
    return recommendations

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is None:
                user = authenticate(email=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

def get_country_from_ip(ip_address):
    try:
        response = requests.get(f"https://ipapi.co/{ip_address}/json/")
        data = response.json()
        return data.get('country_code')
    except Exception:
        return None

@login_required
def profile(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, instance=request.user.userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=request.user.userprofile)

    streak, created = UserStreak.objects.get_or_create(user=request.user)
    achievements = Achievement.objects.filter(user=request.user)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'streak': streak,
        'achievements': achievements,
        'countries': list(countries),
    }
    return render(request, 'tracker/profile.html', context)

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


def home(request):
    return render(request, 'home.html')
  
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def logout(request):
    auth_logout(request)
    return redirect('login')

@login_required
def log_meal(request):
    if request.method == 'POST':
        form = MealForm(request.POST, user=request.user)
        if form.is_valid():
            meal = form.save(commit=False)
            meal.user = request.user
            meal.save()

            if nutritional_info := get_nutritional_info(
                f"{meal.portion_size} {meal.name}"
            ):
                nutritional_value = NutritionalValue.objects.create(
                    calories=nutritional_info.get('calories', 0),
                    protein=nutritional_info.get('protein', 0),
                    carbs=nutritional_info.get('carbs', 0),
                    fat=nutritional_info.get('fat', 0),
                    fiber=nutritional_info.get('fiber', 0),
                    sugar=nutritional_info.get('sugar', 0),
                    sodium=nutritional_info.get('sodium', 0),
                    cholesterol=nutritional_info.get('cholesterol', 0),
                    saturated_fat=nutritional_info.get('saturated_fat', 0),
                    unsaturated_fat=nutritional_info.get('unsaturated_fat', 0),
                    trans_fat=nutritional_info.get('trans_fat', 0),
                    vitamin_a=nutritional_info.get('vitamin_a', 0),
                    vitamin_c=nutritional_info.get('vitamin_c', 0),
                    calcium=nutritional_info.get('calcium', 0),
                    iron=nutritional_info.get('iron', 0)
                )
                meal.nutritional_value = nutritional_value
                meal.save()

            messages.success(request, 'Meal logged successfully!')
            return redirect('dashboard')
    else:
        form = MealForm(user=request.user)

    context = {
        'form': form,
    }
    return render(request, 'tracker/log_meal.html', context)

@login_required
def log_symptom(request):
    if request.method == 'POST':
        form = SymptomForm(request.POST)
        if form.is_valid():
            symptom = form.save(commit=False)
            symptom.user = request.user
            symptom.save()
            check_and_award_achievements(request.user)
            messages.success(request, 'Symptom logged successfully!')
            return redirect('dashboard')
    else:
        form = SymptomForm()
    return render(request, 'tracker/log_symptom.html', {'form': form})

@login_required
def dashboard(request):
    end_date = request.GET.get('end_date')
    start_date = request.GET.get('start_date')

    if end_date:
        end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
        end_date = timezone.now().date()

    if start_date:
        start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
    else:
        start_date = end_date - timedelta(days=30)

    meals = Meal.objects.filter(user=request.user, date_time__date__range=[start_date, end_date]).order_by('-date_time')
    symptoms = Symptom.objects.filter(user=request.user, date_time__date__range=[start_date, end_date]).order_by('-date_time')

    # Prepare data for charts
    meal_chart_data = prepare_chart_data(meals, start_date, end_date)
    symptom_chart_data = prepare_chart_data(symptoms, start_date, end_date)

    # Fetch the latest health metrics for the user
    latest_health_metrics = HealthMetricLog.objects.filter(user=request.user).order_by('-date').first()

    # Ensure user profile exists
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    nutritional_goals = calculate_nutritional_goals(user_profile, latest_health_metrics)

    # Calculate average nutritional intake
    avg_nutrition = meals.aggregate(
        avg_calories=Avg('nutritional_value__calories'),
        avg_protein=Avg('nutritional_value__protein'),
        avg_carbs=Avg('nutritional_value__carbs'),
        avg_fat=Avg('nutritional_value__fat'),
        avg_fiber=Avg('nutritional_value__fiber')
    )

    # Pagination
    meal_paginator = Paginator(meals, 10)
    symptom_paginator = Paginator(symptoms, 10)

    meal_page = request.GET.get('meal_page')
    symptom_page = request.GET.get('symptom_page')

    try:
        meals = meal_paginator.page(meal_page)
    except PageNotAnInteger:
        meals = meal_paginator.page(1)
    except EmptyPage:
        meals = meal_paginator.page(meal_paginator.num_pages)

    try:
        symptoms = symptom_paginator.page(symptom_page)
    except PageNotAnInteger:
        symptoms = symptom_paginator.page(1)
    except EmptyPage:
        symptoms = symptom_paginator.page(symptom_paginator.num_pages)

    context = {
        'meals': meals,
        'symptoms': symptoms,
        'start_date': start_date,
        'end_date': end_date,
        'meal_chart_data': json.dumps(meal_chart_data),
        'symptom_chart_data': json.dumps(symptom_chart_data),
        'health_metrics': latest_health_metrics,
        'avg_nutrition': avg_nutrition,
        'nutritional_goals': nutritional_goals,
        'meal_page': meal_page,
        'symptom_page': symptom_page,
    }

    return render(request, 'tracker/dashboard.html', context)

def prepare_chart_data(queryset, start_date, end_date):
    date_counts = queryset.values('date_time__date').annotate(count=Count('id')).order_by('date_time__date')
    date_dict = {item['date_time__date']: item['count'] for item in date_counts}
    
    chart_data = []
    current_date = start_date
    while current_date <= end_date:
        chart_data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'count': date_dict.get(current_date, 0)
        })
        current_date += timedelta(days=1)
    
    return chart_data

@login_required
def export_meals_csv(request):
    meals = Meal.objects.filter(user=request.user).order_by('-date_time')
    fields = ['meal_type', 'date_time', 'ingredients', 'portion_size', 'notes']
    return export_as_csv(meals, fields, 'meals_report')

@login_required
def export_symptoms_csv(request):
    symptoms = Symptom.objects.filter(user=request.user).order_by('-date_time')
    fields = ['date_time', 'description', 'severity']
    return export_as_csv(symptoms, fields, 'symptoms_report')
  
@login_required
def food_recommendations(request):
    user_profile = request.user.userprofile
    recommendations = FoodRecommendation.objects.filter(user_profile=user_profile)

    # If no recommendations exist or they're older than a week, generate new ones
    if not recommendations.exists() or (timezone.now() - recommendations.latest('created_at').created_at).days > 7:
        generate_food_recommendations(user_profile)
        recommendations = FoodRecommendation.objects.filter(user_profile=user_profile)

    # Get user's recent meals and health metrics
    recent_meals = Meal.objects.filter(user=request.user, date_time__gte=timezone.now() - timedelta(days=30))
    recent_health_metrics = HealthMetricLog.objects.filter(user=request.user, date__gte=timezone.now() - timedelta(days=30))

    # Calculate average nutritional intake
    avg_nutrition = recent_meals.aggregate(
        avg_calories=Avg('nutritional_value__calories'),
        avg_protein=Avg('nutritional_value__protein'),
        avg_carbs=Avg('nutritional_value__carbs'),
        avg_fat=Avg('nutritional_value__fat'),
        avg_fiber=Avg('nutritional_value__fiber'),
        avg_sugar=Avg('nutritional_value__sugar'),
        avg_sodium=Avg('nutritional_value__sodium'),
        avg_cholesterol=Avg('nutritional_value__cholesterol'),
        avg_saturated_fat=Avg('nutritional_value__saturated_fat'),
        avg_unsaturated_fat=Avg('nutritional_value__unsaturated_fat'),
        avg_trans_fat=Avg('nutritional_value__trans_fat'),
        avg_vitamin_a=Avg('nutritional_value__vitamin_a'),
        avg_vitamin_c=Avg('nutritional_value__vitamin_c'),
        avg_calcium=Avg('nutritional_value__calcium'),
        avg_iron=Avg('nutritional_value__iron')
    )

    # Get latest health metrics or None if no metrics exist
    latest_health_metrics = recent_health_metrics.order_by('-date').first()

    # Determine nutritional goals based on user profile and health metrics
    nutritional_goals = calculate_nutritional_goals(user_profile, latest_health_metrics)

    # Compare current intake with goals and generate insights
    nutritional_insights = generate_nutritional_insights(avg_nutrition, nutritional_goals)

    # Enhance recommendations with specific benefits and reasons
    enhanced_recommendations = []
    for rec in recommendations:
        enhanced_rec = {
            'recommendation': rec.recommendation,
            'description': rec.description,
            'image_url': rec.image_url or 'https://via.placeholder.com/300x200?text=Healthy+Food',
            'benefits': get_food_benefits(rec.recommendation, nutritional_insights),
            'reason': get_recommendation_reason(rec.recommendation, nutritional_insights, user_profile)
        }
        enhanced_recommendations.append(enhanced_rec)

    context = {
        'recommendations': enhanced_recommendations,
        'nutritional_insights': nutritional_insights,
        'avg_nutrition': avg_nutrition,
        'nutritional_goals': nutritional_goals
    }
    return render(request, 'tracker/food_recommendations.html', context)

def calculate_nutritional_goals(user_profile, health_metrics):
    # Default values
    default_weight = 70  # kg
    default_height = 170  # cm
    default_age = 30  # years
    default_activity_factor = 1.2  # Sedentary

    # Use health metrics if available, otherwise use defaults
    weight = health_metrics.weight if health_metrics and health_metrics.weight else default_weight
    height = user_profile.height if hasattr(user_profile, 'height') and user_profile.height else default_height
    age = user_profile.age if hasattr(user_profile, 'age') and user_profile.age else default_age

    # Base calorie needs (Mifflin-St Jeor Equation)
    if hasattr(user_profile, 'gender') and user_profile.gender == 'F':
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    elif hasattr(user_profile, 'gender') and user_profile.gender == 'M':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 78
    # Activity factor
    if hasattr(user_profile, 'activity_level'):
        activity_factors = {
            'sedentary': 1.2,
            'lightly_active': 1.375,
            'moderately_active': 1.55,
            'very_active': 1.725,
            'extra_active': 1.9
        }
        activity_factor = activity_factors.get(user_profile.activity_level, default_activity_factor)
    else:
        activity_factor = default_activity_factor

    calorie_needs = bmr * activity_factor

    # Adjust for weight goals
    if hasattr(user_profile, 'weight_goal'):
        if user_profile.weight_goal == 'lose':
            calorie_needs *= 0.85
        elif user_profile.weight_goal == 'gain':
            calorie_needs *= 1.15

    # Macronutrient distribution
    protein_calories = calorie_needs * 0.25
    carb_calories = calorie_needs * 0.5
    fat_calories = calorie_needs * 0.25

    return {
        'calories': round(calorie_needs),
        'protein': round(protein_calories / 4),  # 4 calories per gram of protein
        'carbs': round(carb_calories / 4),  # 4 calories per gram of carb
        'fat': round(fat_calories / 9),  # 9 calories per gram of fat
        'fiber': 25 if hasattr(user_profile, 'gender') and user_profile.gender == 'F' else 38  # Based on general recommendations
    }

def get_food_benefits(food, insights):
    benefits_db = {
        'Salmon': ['High in omega-3 fatty acids', 'Good source of protein', 'Rich in vitamin D'],
        'Spinach': ['Rich in iron and vitamins', 'High in fiber', 'Low in calories'],
        'Quinoa': ['Complete protein source', 'High in fiber', 'Rich in minerals'],
        'Blueberries': ['High in antioxidants', 'May improve brain function', 'Low in calories'],
        'Almonds': ['Good source of healthy fats', 'High in vitamin E', 'May lower cholesterol'],
        'Greek Yogurt': ['High in protein', 'Good source of probiotics', 'Rich in calcium'],
        'Sweet Potato': ['High in vitamin A', 'Good source of fiber', 'Rich in antioxidants'],
        'Broccoli': ['High in vitamin C', 'Good source of fiber', 'May have anti-cancer properties'],
        'Eggs': ['High-quality protein source', 'Rich in choline', 'Contains antioxidants'],
        'Avocado': ['High in healthy fats', 'Good source of fiber', 'Rich in potassium']
    }
    
    benefits = benefits_db.get(food, ['Nutritious choice'])
    
    # Add personalized benefits based on insights
    if 'protein intake is low' in insights and 'protein' in ' '.join(benefits).lower():
        benefits.append('Helps meet your protein needs')
    if 'fiber intake is low' in insights and 'fiber' in ' '.join(benefits).lower():
        benefits.append('Helps increase your fiber intake')
    
    return benefits[:3]  # Return top 3 benefits

def generate_food_recommendations(user_profile):
    # Get recent meals and health metrics
    recent_meals = Meal.objects.filter(user=user_profile.user, date_time__gte=timezone.now() - timedelta(days=30))
    recent_health_metrics = HealthMetricLog.objects.filter(user=user_profile.user, date__gte=timezone.now() - timedelta(days=30))
    latest_health_metrics = recent_health_metrics.order_by('-date').first()

    # Calculate average nutritional intake
    avg_nutrition = recent_meals.aggregate(
        avg_calories=Avg('nutritional_value__calories'),
        avg_protein=Avg('nutritional_value__protein'),
        avg_carbs=Avg('nutritional_value__carbs'),
        avg_fat=Avg('nutritional_value__fat'),
        avg_fiber=Avg('nutritional_value__fiber'),
        avg_sugar=Avg('nutritional_value__sugar'),
        avg_sodium=Avg('nutritional_value__sodium'),
        avg_cholesterol=Avg('nutritional_value__cholesterol'),
        avg_saturated_fat=Avg('nutritional_value__saturated_fat'),
        avg_unsaturated_fat=Avg('nutritional_value__unsaturated_fat'),
        avg_trans_fat=Avg('nutritional_value__trans_fat'),
        avg_vitamin_a=Avg('nutritional_value__vitamin_a'),
        avg_vitamin_c=Avg('nutritional_value__vitamin_c'),
        avg_calcium=Avg('nutritional_value__calcium'),
        avg_iron=Avg('nutritional_value__iron')
    )

    # Get nutritional goals
    nutritional_goals = calculate_nutritional_goals(user_profile, latest_health_metrics)

    # Generate insights
    insights = generate_nutritional_insights(avg_nutrition, nutritional_goals)

    # List of foods to recommend
    foods_to_recommend = [
        'Salmon', 'Spinach', 'Quinoa', 'Blueberries', 'Almonds',
        'Greek Yogurt', 'Sweet Potato', 'Broccoli', 'Eggs', 'Avocado'
    ]

    # Filter foods based on dietary preferences
    if user_profile.dietary_preferences == 'vegetarian':
        foods_to_recommend = [f for f in foods_to_recommend if f not in ['Salmon', 'Eggs']]
    elif user_profile.dietary_preferences == 'vegan':
        foods_to_recommend = [f for f in foods_to_recommend if f not in ['Salmon', 'Eggs', 'Greek Yogurt']]

    # Generate recommendations
    recommendations = []
    for food in random.sample(foods_to_recommend, min(5, len(foods_to_recommend))):
        benefits = get_food_benefits(food, insights)
        reason = get_recommendation_reason(food, insights, user_profile)
        
        recommendation = FoodRecommendation(
            user_profile=user_profile,
            recommendation=food,
            description=f"{food} is recommended because it {reason}",
            image_url=f"https://example.com/images/{food.lower().replace(' ', '_')}.jpg"  # Replace with actual image URLs
        )
        recommendations.append(recommendation)

    # Save recommendations
    FoodRecommendation.objects.bulk_create(recommendations)

def generate_nutritional_insights(avg_nutrition, goals):
    insights = []
    for nutrient, avg_value in avg_nutrition.items():
        if avg_value:
            if goal := goals.get(nutrient.split('_')[1]):
                if avg_value < goal * 0.9:
                    insights.append(f"Your {nutrient.split('_')[1]} intake is low. Try to increase it.")
                elif avg_value > goal * 1.1:
                    insights.append(f"Your {nutrient.split('_')[1]} intake is high. Consider reducing it.")
    return insights

def get_recommendation_reason(recommendation, nutritional_insights, user_profile):
    reasons = []

    # Check if the recommendation aligns with the user's dietary preferences
    if user_profile.dietary_preferences and any(pref.lower() in recommendation.lower() for pref in user_profile.dietary_preferences.split(',')):
        reasons.append(f"Aligns with your dietary preference of {user_profile.dietary_preferences}")

    # Check nutritional insights
    if 'low_protein' in nutritional_insights and 'protein' in recommendation.lower():
        reasons.append("Helps increase your protein intake")
    if 'high_carbs' in nutritional_insights and 'low-carb' in recommendation.lower():
        reasons.append("Helps reduce your carbohydrate intake")
    if 'low_fiber' in nutritional_insights and 'fiber' in recommendation.lower():
        reasons.append("Increases your fiber intake")

    # Add more checks based on other nutritional insights and user profile data

    if not reasons:
        reasons.append("Generally beneficial for a balanced diet")

    return "; ".join(reasons)

@login_required
def diet_plans(request):
    user_profile = request.user.userprofile
    today = timezone.now().date()

    diet_plan, created = DietPlan.objects.get_or_create(
        user_profile=user_profile,
        plan_date=today
    )

    if created:
        meals = generate_diet_plan(user_profile, start_date=today)
        diet_plan.meals = meals
        diet_plan.save()

    context = {
        'diet_plan': diet_plan
    }
    return render(request, 'tracker/diet_plans.html', context)

@login_required
def insights(request):
    try:
        # Allow customization of the analysis period
        days = int(request.GET.get('days', 30))
        analytics = analyze_meal_symptom_trends(request.user, days=days)

        context = {
            'analytics': analytics,
            'days': days
        }
        return render(request, 'tracker/insights.html', context)
    except ValueError:
        return HttpResponse("Invalid 'days' parameter. Please provide a valid number.", status=400)
    except Exception as e:
        # Log the error here
        return HttpResponse("An error occurred while generating insights.", status=500)

@login_required
def edit_meal(request, meal_id):
    meal = get_object_or_404(Meal, id=meal_id, user=request.user)
    if request.method == 'POST':
        form = MealForm(request.POST, instance=meal)
        if form.is_valid():
            updated_meal = form.save(commit=False)
            updated_meal.user = request.user
            updated_meal.save()

            if nutritional_info := get_nutritional_info(
                f"{updated_meal.portion_size} {updated_meal.name}"
            ):
                if updated_meal.nutritional_value:
                    nutritional_value = updated_meal.nutritional_value
                    for key, value in nutritional_info.items():
                        setattr(nutritional_value, key, value)
                    nutritional_value.save()
                else:
                    nutritional_value = NutritionalValue.objects.create(
                        calories=nutritional_info.get('calories', 0),
                        protein=nutritional_info.get('protein', 0),
                        carbs=nutritional_info.get('carbs', 0),
                        fat=nutritional_info.get('fat', 0),
                        fiber=nutritional_info.get('fiber', 0),
                        sugar=nutritional_info.get('sugar', 0),
                        sodium=nutritional_info.get('sodium', 0),
                        cholesterol=nutritional_info.get('cholesterol', 0),
                        saturated_fat=nutritional_info.get('saturated_fat', 0),
                        unsaturated_fat=nutritional_info.get('unsaturated_fat', 0),
                        trans_fat=nutritional_info.get('trans_fat', 0),
                        vitamin_a=nutritional_info.get('vitamin_a', 0),
                        vitamin_c=nutritional_info.get('vitamin_c', 0),
                        calcium=nutritional_info.get('calcium', 0),
                        iron=nutritional_info.get('iron', 0)
                    )
                    updated_meal.nutritional_value = nutritional_value
                    updated_meal.save()

            # Update nutritional insights
            updated_meal.nutritional_insights = analyze_meal_description(updated_meal.ingredients)
            updated_meal.save()

            messages.success(request, 'Meal updated successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = MealForm(instance=meal)
    return render(request, 'tracker/edit_meal.html', {'form': form, 'meal': meal})

@login_required
def delete_meal(request, meal_id):
    meal = get_object_or_404(Meal, id=meal_id, user=request.user)
    if request.method == 'POST':
        meal.delete()
        messages.success(request, 'Meal deleted successfully!')
        return redirect('dashboard')
    return render(request, 'tracker/delete_meal.html', {'meal': meal})

@login_required
def edit_symptom(request, symptom_id):
    symptom = get_object_or_404(Symptom, id=symptom_id, user=request.user)
    if request.method == 'POST':
        form = SymptomForm(request.POST, instance=symptom)
        if form.is_valid():
            form.save()
            messages.success(request, 'Symptom updated successfully!')
            return redirect('dashboard')
    else:
        form = SymptomForm(instance=symptom)
    return render(request, 'tracker/edit_symptom.html', {'form': form, 'symptom': symptom})

@login_required
def delete_symptom(request, symptom_id):
    symptom = get_object_or_404(Symptom, id=symptom_id, user=request.user)
    if request.method == 'POST':
        symptom.delete()
        messages.success(request, 'Symptom deleted successfully!')
        return redirect('dashboard')
    return render(request, 'tracker/delete_symptom.html', {'symptom': symptom})

def check_and_award_achievements(user):
    today = timezone.now().date()
    
    # Check for streak
    streak, created = UserStreak.objects.get_or_create(user=user)
    if streak.last_log_date == today - timezone.timedelta(days=1):
        streak.current_streak += 1
        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak
    elif streak.last_log_date != today:
        streak.current_streak = 1
    streak.last_log_date = today
    streak.save()

    # Award streak achievements
    streak_achievements = [
        (7, "7 Day Streak", "Logged for 7 consecutive days", "fa-fire"),
        (30, "30 Day Streak", "Logged for 30 consecutive days", "fa-fire-alt"),
        (100, "100 Day Streak", "Logged for 100 consecutive days", "fa-burn"),
    ]

    for days, name, description, icon in streak_achievements:
        if streak.longest_streak >= days and not Achievement.objects.filter(user=user, name=name).exists():
            Achievement.objects.create(user=user, name=name, description=description, icon=icon)

    # Check total logs
    total_logs = user.meal_set.count() + user.symptom_set.count()
    log_achievements = [
        (50, "50 Logs", "Logged 50 meals or symptoms", "fa-book"),
        (100, "100 Logs", "Logged 100 meals or symptoms", "fa-books"),
        (500, "500 Logs", "Logged 500 meals or symptoms", "fa-bookshelf"),
    ]

    for count, name, description, icon in log_achievements:
        if total_logs >= count and not Achievement.objects.filter(user=user, name=name).exists():
            Achievement.objects.create(user=user, name=name, description=description, icon=icon)

@login_required
def frequencies(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date and end_date:
        start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
        end_date = timezone.now().date()
        start_date = end_date - timezone.timedelta(days=30)

    meals = Meal.objects.filter(user=request.user, date_time__date__range=[start_date, end_date])
    symptoms = Symptom.objects.filter(user=request.user, date_time__date__range=[start_date, end_date])

    meal_chart_data = list(
        meals.annotate(date=TruncDate('date_time'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )

    symptom_chart_data = list(
        symptoms.annotate(date=TruncDate('date_time'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )

    # Convert dates to string format for JSON serialization
    for item in meal_chart_data:
        item['date'] = item['date'].strftime('%Y-%m-%d')

    for item in symptom_chart_data:
        item['date'] = item['date'].strftime('%Y-%m-%d')

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'meals': meals,
        'symptoms': symptoms,
        'meal_chart_data': json.dumps(meal_chart_data),
        'symptom_chart_data': json.dumps(symptom_chart_data),
    }

    return render(request, 'tracker/frequencies.html', context)

@login_required
def generate_diet_plan(request):
    # Get user's meals and symptoms from the last 30 days
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    user_meals = Meal.objects.filter(user=request.user, date_time__range=[start_date, end_date])
    user_symptoms = Symptom.objects.filter(user=request.user, date_time__range=[start_date, end_date])

    safe_meals = [
        meal
        for meal in user_meals
        if not user_symptoms.filter(
            date_time__gt=meal.date_time,
            date_time__lte=meal.date_time + timedelta(hours=4),
        ).exists()
    ]
    # Extract ingredients from safe meals
    safe_ingredients = set()
    for meal in safe_meals:
        safe_ingredients.update(meal.ingredients.split(', '))

    # If no safe ingredients found, use all FoodItems
    if not safe_ingredients:
        safe_ingredients = set(FoodItem.objects.values_list('name', flat=True))

    # Generate a weekly meal plan
    meal_plan = []
    for _ in range(7):  # 7 days
        daily_meals = []
        for meal_type in ['Breakfast', 'Lunch', 'Dinner']:
            if safe_meals:
                base_meal = random.choice(safe_meals)
                ingredients = list(base_meal.ingredients.split(', '))
                # Add some variety by swapping out 1-2 ingredients
                for _ in range(random.randint(1, 2)):
                    if ingredients and safe_ingredients:
                        ingredients[random.randint(0, len(ingredients)-1)] = random.choice(list(safe_ingredients))
                daily_meals.append({
                    'type': meal_type,
                    'ingredients': ', '.join(ingredients)
                })
            elif safe_ingredients:
                daily_meals.append({
                    'type': meal_type,
                    'ingredients': ', '.join(random.sample(list(safe_ingredients), min(3, len(safe_ingredients))))
                })
            else:
                daily_meals.append({
                    'type': meal_type,
                    'ingredients': 'No safe ingredients found. Please consult a nutritionist.'
                })
        meal_plan.append(daily_meals)

    context = {
        'meal_plan': meal_plan,
        'safe_ingredients': list(safe_ingredients)[:20],  # Limit to 20 ingredients for display
    }
    return render(request, 'tracker/diet_plan.html', context)

@login_required
def meal_detail(request, meal_id):
    meal = get_object_or_404(Meal, id=meal_id, user=request.user)
    return render(request, 'tracker/meal_detail.html', {'meal': meal})

@login_required
def meal_list(request):
    meals = Meal.objects.filter(user=request.user).order_by('-date_time')
    paginator = Paginator(meals, 10)
    page = request.GET.get('page')
    try:
        meals = paginator.page(page)
    except PageNotAnInteger:
        meals = paginator.page(1)
    except EmptyPage:
        meals = paginator.page(paginator.num_pages)
    return render(request, 'tracker/meal_list.html', {'meals': meals})

@login_required
def get_meal_details(request, meal_id):
    meal = get_object_or_404(Meal, id=meal_id, user=request.user)
    return JsonResponse({
        'meal_type': meal.meal_type.id if meal.meal_type else '',
        'ingredients': meal.ingredients,
        'portion_size': meal.portion_size,
        'notes': meal.notes,
    })

@login_required
def log_health_metrics(request):
    today = timezone.now().date()
    existing_log = HealthMetricLog.objects.filter(user=request.user, date=today).first()

    if request.method == 'POST':
        form = (
            HealthMetricForm(request.POST, instance=existing_log)
            if existing_log
            else HealthMetricForm(request.POST)
        )
        if form.is_valid():
            health_metric = form.save(commit=False)
            health_metric.user = request.user
            health_metric.date = today  # Ensure the date is set to today
            health_metric.save()
            messages.success(request, 'Health metrics logged successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    elif existing_log:
        form = HealthMetricForm(instance=existing_log)
    else:
        form = HealthMetricForm()

    context = {
        'form': form,
        'is_update': existing_log is not None
    }
    return render(request, 'tracker/log_health_metrics.html', context)

@login_required
def update_nutritional_goals(request):
    profile = request.user.userprofile
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'tracker/update_nutritional_goals.html', {'form': form})

@login_required
def health_report(request):
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    meals = Meal.objects.filter(user=request.user, date_time__date__range=[start_date, end_date])
    health_metrics = HealthMetricLog.objects.filter(user=request.user, date__range=[start_date, end_date])
    
    daily_calories = meals.values('date_time__date').annotate(total_calories=Sum('nutritional_value__calories'))
    weight_trend = health_metrics.values('date', 'weight')
    blood_pressure = health_metrics.values('date', 'blood_pressure_systolic', 'blood_pressure_diastolic')
    
    avg_systolic = health_metrics.aggregate(Avg('blood_pressure_systolic'))['blood_pressure_systolic__avg']
    avg_diastolic = health_metrics.aggregate(Avg('blood_pressure_diastolic'))['blood_pressure_diastolic__avg']
    
    if avg_systolic is not None and avg_diastolic is not None:
        avg_blood_pressure = f"{avg_systolic:.0f}/{avg_diastolic:.0f}"
    else:
        avg_blood_pressure = "N/A"
    
    context = {
        'daily_calories': json.dumps([{'date': item['date_time__date'].strftime('%Y-%m-%d'), 'calories': item['total_calories'] or 0} for item in daily_calories]),
        'weight_trend': json.dumps([{'date': item['date'].strftime('%Y-%m-%d'), 'weight': item['weight'] or 0} for item in weight_trend]),
        'blood_pressure': json.dumps([{'date': item['date'].strftime('%Y-%m-%d'), 'systolic': item['blood_pressure_systolic'] or 0, 'diastolic': item['blood_pressure_diastolic'] or 0} for item in blood_pressure]),
        'avg_calories': meals.aggregate(Avg('nutritional_value__calories'))['nutritional_value__calories__avg'] or 0,
        'avg_weight': health_metrics.aggregate(Avg('weight'))['weight__avg'] or 0,
        'avg_blood_pressure': avg_blood_pressure,
    }
    
    return render(request, 'tracker/health_report.html', context)