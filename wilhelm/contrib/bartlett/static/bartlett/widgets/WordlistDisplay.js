// A Word list Display Object.
var WordlistDisplayObject = function(
                    domtag, // The DOM element to which we attach.
                    gatewayurl, // An object with values for the durations.
                    ping_uid
    ) {

    var self = Widget({HeadTag: $(domtag),
                       gatewayurl: gatewayurl,
                       ping_uid: ping_uid});

    self.word_box = self.HeadTag.find('#word_box');
    self.foo_word = self.HeadTag.find('#foo_word');

    self.memory_word = self.HeadTag.find('#memory_word');
  
    // What element is the "tag" for stimulus display.
    self.StimulusTag = self.memory_word;
 
    // Parse the incoming json data.
    self.ParseJsonData = function(data) {

        self.Stimuli = data.wordlist;
        self.StartButton.text(data.start_wordlist_msg);
        self.timings = {
             fadeInDuration: parseFloat(data.fadeInDuration) *1000,
             fadeOutDuration: parseFloat(data.fadeOutDuration) * 1000,
             stimulusDuration: parseFloat(data.stimulusDuration)*1000,
             isi: parseFloat(data.isi) * 1000
            };
    }

    self.OnButtonPress = function() {};

    self.OnStimulusTimeOut = function() {
        
        // Assemble results as an object.
        var results = {
            order: self.i,
            word: self.Stimuli[self.i],
            onset: self.StimulusDisplayed,
            }

        self.TerminateStimulusDisplay(results);
    };

    // Just to see how it would be done.
    self.PrimeTargetDisplayStimulus = function(stimulus) {
        self.foo_word.hide()
        .text('prime')
        .fadeIn(0).delay(1000)
        .fadeOut(0,function(){self.memory_word.hide().text(stimulus);self.StimulusDequeue(); });
    };

    self.DisplayStimulus = function(stimulus) {
        self.memory_word.hide().text(stimulus);
        self.StimulusDequeue(); 
    };


    return self;

}
