document.addEventListener('DOMContentLoaded', function() {
  var sidebarToggle = document.getElementById('sidebarToggle');
  var sidebar = document.getElementById('sidebar');

  if (sidebarToggle && sidebar) {
      sidebarToggle.addEventListener('click', function() {
          sidebar.classList.toggle('active');
      });

      // Close sidebar when clicking outside of it
      document.addEventListener('click', function(event) {
          var isClickInsideSidebar = sidebar.contains(event.target);
          var isClickOnToggleButton = sidebarToggle.contains(event.target);

          if (!isClickInsideSidebar && !isClickOnToggleButton && sidebar.classList.contains('active')) {
              sidebar.classList.remove('active');
          }
      });
  }
});