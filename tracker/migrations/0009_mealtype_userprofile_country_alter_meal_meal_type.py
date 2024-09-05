from django.db import migrations, models
import django.db.models.deletion
from django_countries.fields import CountryField

def create_meal_types_and_convert(apps, schema_editor):
    MealType = apps.get_model('tracker', 'MealType')
    Meal = apps.get_model('tracker', 'Meal')

    meal_types = {
        meal_type: MealType.objects.create(
            name=meal_type, country='US', ingredients=''
        )
        for meal_type in ['Breakfast', 'Lunch', 'Dinner', 'Snack']
    }
    # Update existing Meals
    for meal in Meal.objects.all():
        meal_type = meal_types.get(meal.meal_type, meal_types['Snack'])
        meal.meal_type_new = meal_type
        meal.save()

class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0008_meal_nutritional_insights'),
    ]

    operations = [
        migrations.CreateModel(
            name='MealType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('country', CountryField()),
                ('ingredients', models.TextField()),
            ],
        ),
        migrations.AddField(
            model_name='userprofile',
            name='country',
            field=CountryField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='meal',
            name='meal_type_new',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='tracker.mealtype'),
        ),
        migrations.RunPython(create_meal_types_and_convert),
        migrations.RemoveField(
            model_name='meal',
            name='meal_type',
        ),
        migrations.RenameField(
            model_name='meal',
            old_name='meal_type_new',
            new_name='meal_type',
        ),
    ]