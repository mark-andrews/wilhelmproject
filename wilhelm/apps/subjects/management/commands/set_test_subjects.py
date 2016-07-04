from django.core.management.base import BaseCommand, CommandError
from apps.subjects.models import Subject

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--file', '-f',
                            dest='filename',
                            required=True,
                            help='The name of the file with test subject uids.')


    def handle(self, *args, **options):
        try:

            
            with open(options['filename'], 'r') as f:
                subject_uids = f.read().strip().split('\n')

            subjects = Subject.objects.set_to_test_subject(subject_uids)

            for subject in subjects:
                self.stdout.write('Subject %s was listed as a test subject.' % subject.user.username)

        except:
            CommandError('Could not add fake subjects.')
