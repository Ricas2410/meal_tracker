# tracker/admin.py
from django.contrib import admin
from .models import UserProfile, Meal, Symptom, FoodItem, FoodRecommendation, DietPlan, Achievement, UserStreak, CountryMeal, HealthMetricLog, NutritionalValue, MealType

class MealAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'date_time', 'meal_type')
    list_filter = ('user', 'date_time', 'meal_type')
    search_fields = ('name', 'ingredients')

class SymptomAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_time', 'description', 'severity')
    list_filter = ('user', 'severity', 'date_time')
    search_fields = ('description',)

class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'calories', 'protein', 'carbs', 'fat')
    search_fields = ('name',)

class FoodRecommendationAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'recommendation', 'created_at')
    list_filter = ('user_profile', 'created_at')
    search_fields = ('recommendation', 'description')

class DietPlanAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'plan_date')
    list_filter = ('user_profile', 'plan_date')
    search_fields = ('notes',)

class AchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'date_earned')
    list_filter = ('user', 'date_earned')
    search_fields = ('name', 'description')

class UserStreakAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_streak', 'longest_streak', 'last_log_date')
    list_filter = ('user', 'last_log_date')

class CountryMealAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'is_ai_generated', 'times_selected')
    list_filter = ('country', 'is_ai_generated')
    search_fields = ('name', 'ingredients')

class HealthMetricLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'weight', 'blood_pressure_systolic', 'blood_pressure_diastolic', 'blood_sugar')
    list_filter = ('user', 'date')

class NutritionalValueAdmin(admin.ModelAdmin):
    list_display = ('meal_data', 'calories', 'protein', 'carbs', 'fat')
    list_filter = ('meal_data__user',)
    search_fields = ('meal_data__name',)

admin.site.register(UserProfile)
admin.site.register(Meal, MealAdmin)
admin.site.register(Symptom, SymptomAdmin)
admin.site.register(FoodItem, FoodItemAdmin)
admin.site.register(FoodRecommendation, FoodRecommendationAdmin)
admin.site.register(DietPlan, DietPlanAdmin)
admin.site.register(Achievement, AchievementAdmin)
admin.site.register(UserStreak, UserStreakAdmin)
admin.site.register(CountryMeal, CountryMealAdmin)
admin.site.register(HealthMetricLog, HealthMetricLogAdmin)
admin.site.register(NutritionalValue, NutritionalValueAdmin)
admin.site.register(MealType)
