from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import Profile

class Command(BaseCommand):
    help = 'Fix profile data integrity issues'

    def handle(self, *args, **options):
        self.stdout.write('Fixing profile data integrity issues...')
        
        # Find users without profiles
        users_without_profiles = User.objects.filter(profile__isnull=True)
        created_count = 0
        
        for user in users_without_profiles:
            profile, created = Profile.objects.get_or_create(user=user)
            if created:
                created_count += 1
                self.stdout.write(f'Created profile for user: {user.username}')
        
        # Find and remove duplicate profiles (keep the first one)
        users_with_multiple_profiles = []
        for user in User.objects.all():
            profiles = Profile.objects.filter(user=user)
            if profiles.count() > 1:
                users_with_multiple_profiles.append(user)
                # Keep the first profile, delete the rest
                profiles_to_delete = profiles[1:]
                for profile in profiles_to_delete:
                    profile.delete()
                self.stdout.write(f'Removed duplicate profiles for user: {user.username}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Profile fix completed:\n'
                f'- Created {created_count} missing profiles\n'
                f'- Fixed {len(users_with_multiple_profiles)} users with duplicate profiles'
            )
        )
