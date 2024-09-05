document.addEventListener('DOMContentLoaded', function() {
  flatpickr(".datetimepicker", {
      enableTime: true,
      dateFormat: "Y-m-d H:i",
      defaultDate: new Date()
  });

  const existingMealSelect = document.getElementById('id_existing_meal');
  const applyButton = document.getElementById('applyExistingMeal');
  const nameInput = document.getElementById('id_name');
  const mealTypeSelect = document.getElementById('id_meal_type');
  const ingredientsTextarea = document.getElementById('id_ingredients');
  const portionSizeInput = document.getElementById('id_portion_size');
  const notesTextarea = document.getElementById('id_notes');

  applyButton.addEventListener('click', function() {
      if (existingMealSelect.value) {
          const selectedOption = existingMealSelect.options[existingMealSelect.selectedIndex];
          nameInput.value = selectedOption.text;
          fetch(`/get_meal_details/${existingMealSelect.value}/`)
              .then(response => response.json())
              .then(data => {
                  mealTypeSelect.value = data.meal_type;
                  ingredientsTextarea.value = data.ingredients;
                  portionSizeInput.value = data.portion_size;
                  notesTextarea.value = data.notes;
              })
              .catch(error => {
                  console.error('Error:', error);
                  alert('An error occurred while fetching meal details. Please try again.');
              });
      } else {
          alert('Please select an existing meal before applying.');
      }
  });
});