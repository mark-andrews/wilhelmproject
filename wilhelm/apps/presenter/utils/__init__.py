from django.contrib.auth.backends import ModelBackend
from apps.subjects import models as subjects_models

class TempSubjectBackend(ModelBackend):

    def authenticate(self, username=None):
        temp_subjects = subjects_models.Subject.objects.filter(
            temp_subject=True, user__username=username
            )
        if temp_subjects:
            return temp_subjects[0].user

