import random

def generate_country_meals(country, num_meals=10):
    country_specific_foods = {
        'United States': ['Hamburger', 'Hot Dog', 'Apple Pie', 'Fried Chicken', 'Macaroni and Cheese', 'Cheeseburger', 'Clam Chowder', 'Buffalo Wings', 'Philly Cheesesteak', 'Barbecue Ribs'],
        'Italy': ['Pizza', 'Pasta', 'Risotto', 'Lasagna', 'Gelato', 'Tiramisu', 'Osso Buco', 'Carbonara', 'Minestrone', 'Bruschetta'],
        'Japan': ['Sushi', 'Ramen', 'Tempura', 'Udon', 'Miso Soup', 'Takoyaki', 'Okonomiyaki', 'Tonkatsu', 'Yakitori', 'Matcha'],
        'Mexico': ['Tacos', 'Enchiladas', 'Guacamole', 'Quesadillas', 'Churros', 'Tamales', 'Pozole', 'Mole', 'Chilaquiles', 'Elote'],
        'India': ['Curry', 'Biryani', 'Tandoori Chicken', 'Naan', 'Samosa', 'Butter Chicken', 'Palak Paneer', 'Dosa', 'Chana Masala', 'Raita'],
        'Nigeria': ['Jollof Rice', 'Egusi Soup', 'Pounded Yam', 'Suya', 'Akara', 'Moi Moi', 'Chin Chin', 'Pepper Soup', 'Eba', 'Dodo'],
        'Ghana': ['Waakye', 'Fufu', 'Banku', 'Jollof Rice', 'Kelewele', 'Red Red', 'Kenkey', 'Tuo Zaafi', 'Shito', 'Groundnut Soup'],
        'Egypt': ['Koshari', 'Ful Medames', 'Molokhia', 'Mahshi', 'Ta\'meya', 'Shawarma', 'Feteer Meshaltet', 'Umm Ali', 'Roz Bel Laban', 'Baba Ganoush'],
        'Hungary': ['Goulash', 'Langos', 'Chicken Paprikash', 'Dobos Torte', 'Stuffed Cabbage', 'Fisherman\'s Soup', 'Kürtőskalács', 'Pörkölt', 'Túrós Csusza', 'Somlói Galuska'],
        # Add more countries and their specific foods as needed
    }

    # Fallback to a general list if the country is not in our database
    default_foods = ['Rice Dish', 'Grilled Meat', 'Vegetable Stew', 'Fish Dish', 'Soup', 'Salad', 'Bread', 'Dumplings', 'Roasted Vegetables', 'Fruit Dessert']

    # Get the list of foods for the specified country, or use default if not found
    country_foods = country_specific_foods.get(country, default_foods)

    # If the country_foods list is shorter than num_meals, we'll need to allow repetitions
    if len(country_foods) < num_meals:
        meals = random.choices(country_foods, k=num_meals)
    else:
        meals = random.sample(country_foods, num_meals)

    # Format the meals as dictionaries with name and ingredients
    formatted_meals = []
    for meal in meals:
        ingredients = [meal] + random.sample(country_foods, k=min(3, len(country_foods)-1))
        formatted_meals.append({
            "name": meal,
            "ingredients": list(set(ingredients))  # Remove duplicates
        })

    return formatted_meals