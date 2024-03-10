from django.dispatch import Signal


superuser_created = Signal()
add_user_to_staff = Signal()
remove_users_from_staff = Signal()