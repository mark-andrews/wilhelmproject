'''
Multipart experiments are going to be featured but not yet. Below is the
collection of multipart experiment code that I've binned here for safe keeping. 
'''

class PartCompletedPlaylistView(PlaylistView):
    '''
    A class for serving the next slide, and taking care of business on the back
    end, when the experiment is paused in ExperimentSessions.
    That's it.
    '''
    def __init__(self, 
                request, 
                experiment_name, 
                part_completed_experiment_session,
                experiment_parts):

        super(PartCompletedPlaylistView, self)\
        .__init__(request, experiment_name)

        self.experiment_parts = experiment_parts
        self.number_of_parts = len(self.experiment_parts)

        self.experiment_session = part_completed_experiment_session
        assert self.experiment_session.status == status_part_completed

        self.parts_completed = ExperimentSessionPart\
        .objects.get_parts_completed(self.experiment_session)

        self.number_of_parts_completed\
        = ExperimentSessionPart.objects.get_number_of_parts_completed(
        self.experiment_session)

        self.last_part_completed = ExperimentSessionPart\
        .objects.get_last_part_completed(self.experiment_session)

        assert self.number_of_parts_completed < self.number_of_parts,\
        stringutils.fill('''If the experiment is in a part-completed state,
        then the number of completed parts should be less than the total number
        of parts. As it stands, we have parts-completed=%d and
        number-of-parts=%d.'''
        % (self.parts_completed, self.number_of_parts))

        assert self.parts_completed > 0,\
        stringutils.fill('''If the experiment is in a part-completed state,
        there should be at least one part of the experiment completed. As it
        stands, we have parts-completed=%d.''' % self.parts_completed)

        assert self.number_of_parts > 1, stringutils.fill('''If the experiment
        is in a part-completed state, there should be more than 1 part to the
        experiment. For experiment "%s", there is only %d part.''' %
        (self.experiment_name, self.number_of_parts))

        assert self.number_of_parts_completed == self.last_part_completed.part\
        + 1, stringutils.fill('''If we are using 0 base indexing, the number of
        completed parts should be equal to the index of the last completed part
        plus 1).''')

        # If we are using n base indexing (e.g. n=0) for experiment parts, then
        # the next part of the experiment will be n + 
        self.next_part = self.last_part_completed.part + 1

    def is_next_part_available(self):
        ''' Experiment parts, in general, are available only during certain
        windows of time. Each part, in general, can not occur before a certain
        date and time and can not occur after another date and time. Also, in
        general, they must not occur before a certain minimum interval has
        elapsed, or after a certain maximum interval has elapsed since the
        previous part was completed.'''

        last_part_date_completed = self.last_part_completed.date_completed

        online_date, offline_date\
        = ExperimentPart.objects.get_online_offline_dates(
            experiment, self.next_part
            )

        available = online_date < now < offline_date

        online_date, offline_date\
        = ExperimentPart.objects.get_online_offline_dates_interval_method(
            experiment, self.next_part, last_part_date_completed
            )

        return available and (online_date < now < offline_date)

    def next_slide(self):
        '''
        Return the next slide in the playlist. To do that, we must move things
        around in the database and update things etc.
        '''

        if not self.is_next_part_available():
            raise NotAvailable()

        else:
            # Turn the experiment_session live.
            self.make_live(self.experiment_session)

            return self._next_slide()

# FIXME
###############################################################
# The experiment parts model is not tested or even used so far.
###############################################################

# Some handy but spurious definitions.
INFINITY = datetime.datetime(year=datetime.MAXYEAR, month=12, day=31)
NEGATIVE_INFINITY = datetime.datetime(year=datetime.MINYEAR, month=1, day=1)
   
class ExperimentPartManager(models.Manager):

    def get_parts(self, experiment):
        return self.filter(experiment=experiment)

    def get_number_of_parts(self, experiment):
        return len(self.get_parts(experiment))

    def get_experiment_part(self, experiment, part):
        return self.get(experiment=experiment, part=part)

    def get_online_offline_dates(self, experiment, part):
        experiment_part = self.get_experiment_part(experiment, part)

        experiment_part_online = experiment_part.online
        experiment_part_offline = experiment_part.offline

        if not experiment_part_online:
            experiment_part_online = NEGATIVE_INFINITY

        if not experiment_part_offline:
            experiment_part_offline = INFINITY

        return experiment_part_online, experiment_part_offline

    def get_online_offline_dates_interval_method(self,
                experiment,
                part,
                last_part_completed):

        experiment_part = self.get_experiment_part(experiment, part)

        experiment_part_minimumInterval = experiment_part.minimumInterval
        experiment_part_maximumInterval = experiment_part.maximumInterval

        if not experiment_part_minimumInterval:
            experiment_part_online = NEGATIVE_INFINITY
        else:
            experiment_part_online = last_part_completed\
            + datetime.timedelta(hours = experiment_part_minimumInterval)

        if not experiment_part_maximumInterval:
            experiment_part_offline = INFINITY
        else:
            experiment_part_offline = last_part_completed\
            + datetime.timedelta(hours = experiment_part_maximumInterval)

        return experiment_part_online, experiment_part_offline


class ExperimentPart(models.Model):

    experiment = models.ForeignKey(Experiment)
    part = models.IntegerField(null=True, default=0)

    #When does the experiment part begin, when does it end.
    #If the online is blank, it can start immediately.
    #If the offline is blank, it goes on forever.
    online = models.DateTimeField(null=True)
    offline = models.DateTimeField(null=True)

    #Minimum and maximum intervals between experiment parts.
    minimum_interval = models.FloatField(null=True)
    maximum_interval = models.FloatField(null=True)

    objects = ExperimentPartManager()

    class Meta:
        unique_together = (('experiment', 'part'),)


# FIXME. This will remain unchecked and untested for now.
class ExperimentSessionPartManager(models.Manager):

    def get_parts_completed(self, experiment_session):
        '''
        Return the number of completed parts in the experiment_session.
        This is all parts that are listed minus those with date_completed is
        null.
        '''
        return self.filter(experiment_session=experiment_session)\
        .exclude(date_completed__isnull=True).order_by('part')

    def get_number_of_parts_completed(self, experiment_session):
        return len(self.get_parts_completed(experiment_session))

    def get_last_part_completed(self, experiment_session):
        return self.get_parts_completed(experiment_session).last()


class ExperimentSessionPart(models.Model):
    objects = ExperimentSessionPartManager()
    experiment_session = models.ForeignKey(ExperimentSession)
    part = models.IntegerField(default=0)
    date_started = models.DateTimeField(null=True, blank=True)
    date_completed = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = (('experiment_session', 'part'),)


class PartCompletedPlaylistViewLauncher(PlaylistViewLauncher):

    def __init__(self, experiment_name):
        super(PartCompletedPlaylistViewLauncher, self).__init__(experiment_name)
        self.playlistview_type = 'PartCompletedPlaylistView'
        self.template_data['launcher_msg'] = self.playlistview_type
