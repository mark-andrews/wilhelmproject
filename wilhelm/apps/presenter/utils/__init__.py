from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from apps.subjects import models as subjects_models
from django.contrib.auth.models import User
from apps.core.utils.sys import checksum as mkhash


class TempSubjectBackend(ModelBackend):

    def authenticate(self, username=None):
        temp_subjects = subjects_models.Subject.objects.filter(
            temp_subject=True, user__username=username
            )
        if temp_subjects:
            return temp_subjects[0].user

class PasswordlessAuthBackend(ModelBackend):
    """Log in to Django without providing a password.

    This is *very* dangerous. Use with extreme caution.

    """
    def authenticate(self, username=None, password=None):

        if mkhash(password) == settings.PASSWORDLESS_AUTH_PASSWORD_HASH:
            try:
                return User.objects.get(username=username)
            except User.DoesNotExist:
                return None
        else:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

