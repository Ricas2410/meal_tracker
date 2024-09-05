import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meal_tracker.settings')
application = get_wsgi_application()

from django.core.management import call_command
call_command('migrate')
