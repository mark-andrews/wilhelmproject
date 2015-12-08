// Display a text.
var TextDisplayObject = function (
                    domtag,
                    gatewayurl, // 
                    ping_uid
    ) {

    var self = Widget({HeadTag: $(domtag),
                       gatewayurl: gatewayurl,
                       ping_uid: ping_uid});

    console.log('text display, do i show ping_uid?');
    console.log(self.ping_uid);

    self.text_box = self.HeadTag.find('#text_box');
    self.title_box = self.HeadTag.find('#title_box');
    self.text_p_box = self.HeadTag.find('#text_p_box');
    self.clock_box = self.HeadTag.find('#clock_box');
    self.countdown_box = self.HeadTag.find('#countdown_box');
    self.move_box = self.HeadTag.find('#move_box');
    self.move_button = self.HeadTag.find('#move_button');

    self.text_box.hide();
    self.move_box.hide();

    self.StimulusTag = self.move_box;

        // Parse the incoming json data.
    self.ParseJsonData = function(data) {

        self.Stimuli = [
            {
                text: data.text,
                title: data.title
            }
        ]

        self.StartButton.text(data.start_text_msg);

        self.timings = {
             max_reading_time: parseFloat(data.maximum_reading_time) * 1000,
             min_reading_time: parseFloat(data.minimum_reading_time) * 1000
        };
        self.timings.stimulusDuration = self.timings.max_reading_time - self.timings.min_reading_time;
        console.log(self.timings.min_reading_time);
        console.log(self.timings.max_reading_time);
        }

    self.UserEvents = 
    [
        {
            listener: self.move_button, 
            EventNames: 'click', 
            Handler:
            function(){clearTimeout(self.StimulusCountdown);self.OnStimulusTimeOut();}
        },
     ];

    self.OnStimulusTimeOut = function() {
            console.log('countdown done');

            var offset = self.timestamp();
            var results = {
                onset: self.StimulusDisplayed,
                offset: offset,
                reading_time: self.timings.min_reading_time + (offset - self.StimulusDisplayed) 
            }      

            self.TerminateStimulusDisplay(results);
    };


    // This is a countdown clock.  If i, an integer, is greater than
    // 0, then display the value of i, decrement i and the call
    // oneself again.
    self.countdown = function (t) {
            if (t >= 0) {
                self.countdown_box.hide().text(t--)
                .fadeIn(0).delay(1000)
                .fadeOut(0, function(){self.countdown(t);});
            }     
    };

    self.DisplayStimulus = function(stimulus) {

        self.text_box.show();
        self.title_box.text(stimulus.title); // Set the text title.
        self.text_p_box.text(stimulus.text); // Set the text.

        setTimeout(self.StimulusDequeue, self.timings.min_reading_time)

        self.countdown(self.timings.max_reading_time/1000);
        
    };

    return self;

}
