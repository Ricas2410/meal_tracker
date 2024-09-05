import requests
import os

NUTRITIONIX_APP_ID = os.environ.get('NUTRITIONIX_APP_ID')
NUTRITIONIX_API_KEY = os.environ.get('NUTRITIONIX_API_KEY')

def get_nutritional_info(query):
    endpoint = "https://trackapi.nutritionix.com/v2/natural/nutrients"
    headers = {
        "x-app-id": NUTRITIONIX_APP_ID,
        "x-app-key": NUTRITIONIX_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "query": query
    }
    
    response = requests.post(endpoint, json=data, headers=headers)
    if response.status_code == 200:
        result = response.json()
        if 'foods' in result and len(result['foods']) > 0:
            food = result['foods'][0]
            return {
                'calories': food['nf_calories'],
                'protein': food['nf_protein'],
                'carbs': food['nf_total_carbohydrate'],
                'fat': food['nf_total_fat']
            }
    return None