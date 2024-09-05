# Generated by Django 5.0.6 on 2024-09-04 18:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0021_remove_nutritionalvalue_meal_meal_meal_type_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='country',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='daily_calcium_goal',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='daily_cholesterol_goal',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='daily_fiber_goal',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='daily_iron_goal',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='daily_saturated_fat_goal',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='daily_sodium_goal',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='daily_sugar_goal',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='daily_trans_fat_goal',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='daily_unsaturated_fat_goal',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='daily_vitamin_a_goal',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='daily_vitamin_c_goal',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='full_name',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='phone_number',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='weight',
        ),
        migrations.AddField(
            model_name='userprofile',
            name='activity_level',
            field=models.CharField(blank=True, choices=[('sedentary', 'Sedentary'), ('lightly_active', 'Lightly Active'), ('moderately_active', 'Moderately Active'), ('very_active', 'Very Active'), ('extra_active', 'Extra Active')], max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='weight_goal',
            field=models.CharField(blank=True, choices=[('lose', 'Lose Weight'), ('maintain', 'Maintain Weight'), ('gain', 'Gain Weight')], max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='daily_calorie_goal',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='daily_carbs_goal',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='daily_fat_goal',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='daily_protein_goal',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='dietary_preferences',
            field=models.TextField(blank=True, default='unknown'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='gender',
            field=models.CharField(blank=True, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], max_length=1, null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='health_conditions',
            field=models.TextField(blank=True, default='N/A'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='known_allergies',
            field=models.TextField(blank=True, default='N/A'),
            preserve_default=False,
        ),
    ]
