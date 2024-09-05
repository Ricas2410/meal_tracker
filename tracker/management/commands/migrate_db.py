from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Apply database migrations'

    def handle(self, *args, **kwargs):
        self.stdout.write('Applying migrations...')
        call_command('migrate')
        self.stdout.write('Migrations applied.')
