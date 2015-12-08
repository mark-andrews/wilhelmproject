// A recognition memory test for words.
var WordRecognitionTestObject = function(
            domtag,
            gatewayurl,
            ping_uid)
 {

    var self = Widget({HeadTag: $(domtag),
                       gatewayurl: gatewayurl,
                       ping_uid: ping_uid});

    // Select all the DOM elements.
    self.word_box = self.HeadTag.find('#word_box');
    self.stimulus_box = self.HeadTag.find('#StimulusBox');
    self.finish_box = self.HeadTag.find('#FinishBox');
    self.test_word = self.HeadTag.find('#test_word');
    self.response_box = self.HeadTag.find('#response_box');
    self.present_button = self.HeadTag.find('#present_button');
    self.absent_button = self.HeadTag.find('#absent_button');

    // Attach some data to the response buttons.
    self.present_button.data('response', 'present');
    self.absent_button.data('response', 'absent');

    // What element is the "tag" for stimulus display.
    // self.StimulusTag = self.test_word;
    self.StimulusTag = self.HeadTag.find('#StimulusTag');
    self.StimulusTag.hide();

    // Parse the incoming json data.
    self.ParseJsonData = function(data) {


        self.Stimuli = data.wordlist;
        self.StartButton.text(data.start_message);
        self.timings = {
             fadeInDuration: parseFloat(data.fadeInDuration) *1000,
             fadeOutDuration: parseFloat(data.fadeOutDuration) * 1000,
             stimulusDuration: parseFloat(data.timeOutDuration) * 1000, 
             isi: parseFloat(data.isi) * 1000
            };
    }

    self.OnButtonPress = function() {

        clearTimeout(self.StimulusCountdown);// Stop the timeout countdown

        var responseTime = self.timestamp()
        
        // Assemble results as an object.
        var results =    {
            order: self.i,
            word: self.Stimuli[self.i],
            onset: self.StimulusDisplayed,
            response: $(this).data('response'),
            responseTime: responseTime,
            latency: responseTime - self.StimulusDisplayed
            }

        self.TerminateStimulusDisplay(results);

        };

    self.OnStimulusTimeOut = function() {
        
        // Assemble results as an object.
        var results =    {
            order: self.i,
            word: self.Stimuli[self.i],
            onset: self.StimulusDisplayed,
            response: null,
            responseTime: null,
            latency: null
            }

        self.TerminateStimulusDisplay(results);
    };

    self.UserEvents = 
    [
        {
            listener: self.present_button,
            EventNames: 'click', 
            Handler: self.OnButtonPress
        },
        {
            listener: self.absent_button,
            EventNames: 'click', 
            Handler: self.OnButtonPress
        }
    ];

    self.DisplayStimulus = function(stimulus) {
        self.test_word.text(stimulus);
        self.StimulusDequeue();
    };

    self._finish = function() {
        self.stimulus_box.hide();
        self.FinishBox.show();
        self.FinishMsg.text('Thank you. Your responses are now being sent.')
        self.send_data();
    };

    return self;

}


