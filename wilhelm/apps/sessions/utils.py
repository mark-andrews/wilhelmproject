from __future__ import absolute_import


from . import models

def get_experiment_sessions(experiment_name, real_subjects_only=True):

    """
    Return experiment sessions from the given experiment.



    """

    experiment_sessions = models.ExperimentSession.objects.filter(
        experiment_version__experiment__class_name = experiment_name)

    if real_subjects_only:
        return experiment_sessions.exclude(subject__temp_subject = True).exclude(subject__test_subject = True)
    else:
        return experiment_sessions
