import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "firstproject.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = os.getenv("DJANGO_ADMIN_USER", "admin")
email = os.getenv("DJANGO_ADMIN_EMAIL", "admin@example.com")
password = os.getenv("DJANGO_ADMIN_PASSWORD", "admin")

if not User.objects.filter(username=username).exists():
    print("🛠  Creating superuser...")
    User.objects.create_superuser(username=username, email=email, password=password)
else:
    print("✅ Superuser already exists.")
