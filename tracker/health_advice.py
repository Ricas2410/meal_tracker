def generate_health_advice(user, daily_intake=None, health_metrics=None):
    advice = []
    user_profile = user.userprofile
    
    # Check BMI
    if user_profile.weight and user_profile.height:
        bmi = user_profile.weight / ((user_profile.height / 100) ** 2)
        if bmi < 18.5:
            advice.append("Your BMI is below the healthy range. Consider consulting a nutritionist for a balanced diet plan.")
        elif bmi > 25:
            advice.append("Your BMI is above the healthy range. Consider incorporating more physical activity and a balanced diet.")
    
    # Check blood pressure
    if user_profile.blood_pressure_systolic and user_profile.blood_pressure_diastolic and (user_profile.blood_pressure_systolic > 140 or user_profile.blood_pressure_diastolic > 90):
        advice.append("Your blood pressure is higher than the normal range. Consider reducing salt intake and increasing physical activity.")
    
    # Check daily intake if provided
    if daily_intake:
        if daily_intake.get('calories', 0) > user_profile.daily_calorie_goal:
            advice.append("You've exceeded your daily calorie goal. Consider adjusting your portion sizes.")
        if daily_intake.get('protein', 0) < user_profile.daily_protein_goal:
            advice.append("Your protein intake is below your daily goal. Consider adding more protein-rich foods to your diet.")
    
    # Check health metrics if provided
    if health_metrics and (health_metrics.blood_sugar and health_metrics.blood_sugar > 100):
        advice.append("Your blood sugar level is higher than normal. Consider reducing your intake of sugary foods and consulting with a healthcare professional.")
    
    # Add more health advice based on other metrics...
    
    return advice