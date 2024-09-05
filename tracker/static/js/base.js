document.addEventListener('DOMContentLoaded', function() {
// skip: avoid-using-var
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');

  if (sidebarToggle && sidebar) {
      sidebarToggle.addEventListener('click', function() {
          sidebar.classList.toggle('active');
      });

      // Close sidebar when clicking outside of it
      document.addEventListener('click', function(event) {
          const isClickInsideSidebar = sidebar.contains(event.target);
          const isClickOnToggleButton = sidebarToggle.contains(event.target);

          if (!isClickInsideSidebar && !isClickOnToggleButton && sidebar.classList.contains('active')) {
              sidebar.classList.remove('active');
          }
      });
  }
});