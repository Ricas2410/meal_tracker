from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from django.contrib import admin
from django.urls import include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # Home and Dashboard
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Meal-related URLs
    path('log_meal/', views.log_meal, name='log_meal'),
    path('edit_meal/<int:meal_id>/', views.edit_meal, name='edit_meal'),
    path('delete_meal/<int:meal_id>/', views.delete_meal, name='delete_meal'),

    # Symptom-related URLs
    path('log_symptom/', views.log_symptom, name='log_symptom'),
    path('edit_symptom/<int:symptom_id>/', views.edit_symptom, name='edit_symptom'),
    path('delete_symptom/<int:symptom_id>/', views.delete_symptom, name='delete_symptom'),

    # Data export
    path('export_meals/', views.export_meals_csv, name='export_meals_csv'),
    path('export_symptoms/', views.export_symptoms_csv, name='export_symptoms_csv'),

    # User authentication
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),

    # Password reset (using Django's built-in views)
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # Data summary
    path('data_summary/', views.data_summary, name='data_summary'),
    path('food_recommendations/', views.food_recommendations, name='food_recommendations'),
    path('insights/', views.insights, name='insights'),
    path('frequencies/', views.frequencies, name='frequencies'),
    path('diet-plan/', views.generate_diet_plan, name='diet_plan'),
    path('meal/<int:meal_id>/', views.meal_detail, name='meal_detail'),
    path('meal-list/', views.meal_list, name='meal_list'),
    path('get_meal_details/<int:meal_id>/', views.get_meal_details, name='get_meal_details'),

    # Health metric logging and nutritional intake tracking
    path('log_health_metrics/', views.log_health_metrics, name='log_health_metrics'),
    path('update_nutritional_goals/', views.update_nutritional_goals, name='update_nutritional_goals'),
    path('log_health_metrics/', views.log_health_metrics, name='log_health_metrics'),
    path('update_nutritional_goals/', views.update_nutritional_goals, name='update_nutritional_goals'),
    path('health_report/', views.health_report, name='health_report'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
