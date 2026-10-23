"""
One-time production setup command.
Loads compendium fixtures and, when credentials are supplied through the
environment, creates the initial superuser.
Skips safely if data already exists.
"""
import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth.models import User


FIXTURES = [
    'compendium/fixtures/initialdata_base.json',
    'compendium/fixtures/initialdata_dependent_fixed.json',
    'compendium/fixtures/weapondice.json',
    'compendium/fixtures/weaponscaling.json',
    'compendium/fixtures/weaponrequirements.json',
    'compendium/fixtures/spelldice.json',
    'compendium/fixtures/spellrequirements.json',
    'compendium/fixtures/spellcharged.json',
    'compendium/fixtures/spellchargeddice.json',
    'compendium/fixtures/backgrounds.json',
    'compendium/fixtures/lineages.json',
    'compendium/fixtures/weaponproffeats_fixture.json',
    'compendium/fixtures/spirits_fixture.json',
    'compendium/fixtures/items_full.json',
    'compendium/fixtures/rings_full.json',
]


class Command(BaseCommand):
    help = 'Load compendium fixtures and create the initial superuser from environment variables'

    def handle(self, *args, **options):
        # Load fixtures
        from compendium.models import Weapon
        if Weapon.objects.count() == 0:
            self.stdout.write('Loading compendium fixtures...')
            for fixture in FIXTURES:
                try:
                    call_command('loaddata', fixture, verbosity=0)
                    self.stdout.write(f'  Loaded {fixture}')
                except Exception as e:
                    self.stdout.write(f'  FAILED {fixture}: {e}')
            self.stdout.write(self.style.SUCCESS('Compendium data loaded.'))
        else:
            self.stdout.write('Compendium data already exists, skipping fixtures.')

        # Create the superuser only from environment variables; credentials
        # never live in code (this repository is public).
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
        if not (username and password):
            self.stdout.write('DJANGO_SUPERUSER_USERNAME/PASSWORD not set, skipping superuser creation.')
            return
        if User.objects.filter(username=username).exists():
            self.stdout.write(f'Superuser "{username}" already exists, skipping.')
            return

        user = User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" created.'))

        # Create UserProfile for the superuser
        from accounts.models import UserProfile
        if not hasattr(user, 'profile'):
            UserProfile.objects.create(
                user=user,
                user_type='permanent',
                subscription_status='active_patron',
                is_admin=True,
                max_characters=50,
                max_campaigns_as_gm=20,
            )
            self.stdout.write(self.style.SUCCESS(f'UserProfile created for "{username}".'))
