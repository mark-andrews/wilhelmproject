// A recognition memory test for words.
var WordRecallTestObject = function(
            domtag,
            gatewayurl,
            ping_uid)
 {

    var self = Widget({HeadTag: $(domtag),
                       gatewayurl: gatewayurl,
                       ping_uid: ping_uid});

    self.results = [];

    // Override timing defaults.
    self.timings['stimulusDuration'] = 180 * 1000;
    self.timings['fadeInDuration'] = 1000;
    self.timings['fadeOutDuration'] = 1000;
    self.timings['isi'] = 0;

    self.recalledwordslist = self.HeadTag.find('#recalledwordslist');
    self.recalledwordsbox = self.HeadTag.find('#recalledwordsbox');
    self.recalledwordsbox.hide();
    self.moreoptionsbutton = self.HeadTag.find('#moreoptionsbutton');
    self.lessoptionsbutton = self.HeadTag.find('#lessoptionsbutton');
    self.resultslist = self.HeadTag.find('#resultslist');
    self.submitresults = self.HeadTag.find('#submitresults')

    self.StimulusTag = self.recalledwordsbox;

    self.finish = function() {
        setTimeout(self.deactivate, 3*1000);
        };

    // Parse the incoming json data.
    self.ParseJsonData = function(data) {
        self.Stimuli = [{}]; // Empty stimuli array.
        self.option_length = parseInt(data.option_length);
        self.StartButton.text(data.start_message);
    }

    self.insertnewwordbox = function () {
        self.recalledwordslist.append($('<li>').append(
        $('<input>').attr({
            type: 'text'
        })));
    };

    self.removewordbox = function () {
        // remove the last input box if empty
        last_box = self.recalledwordslist.find('li').last();
        if (!last_box.find('input').val()) {
            last_box.remove();
        }
    };

    self.focusfirstempty = function () {
        self.recalledwordslist.find('input').filter(function () {
            if ($(this).val() === '') {
                return true;
            }
        }).first().focus();
    };

    self.makeKnewboxes = function (K) {
        for (var i = 0; i < K; i++) {
            self.insertnewwordbox();
        }
    };

    self.getwords = function () {
        var results = [];
        var w = self.recalledwordslist.find('input').filter(function () {
            if ($(this).val()) {
                return true;
            }
        });
        w.each(function () {
            results.push($(this).val().trim());
        });
        
        self.TerminateStimulusDisplay(results);
        
    };

    self.DisplayStimulus = function(stimulus) {
       self.makeKnewboxes(self.option_length);
       self.StimulusDequeue(); 
    }

    self.processfeedback = function(data) {
        console.log('I am processing the feedback.');
        console.log(data);
        self.FinishMsg.text('Thank you. The following words have been recorded and sent.')
        self.resultslist = $('<ol/>').appendTo(self.FinishBox);
        $.each(data, function(index, value) {
            self.resultslist.append($('<li>').append(value));
        });
    }

    self.UserEvents = 
    [
        {
            listener: self.moreoptionsbutton,
            EventNames: 'click', 
            Handler: function(){self.insertnewwordbox();self.focusfirstempty();}
        },
        {
            listener: self.lessoptionsbutton, 
            EventNames: 'click', 
            Handler: function () {self.removewordbox(); self.focusfirstempty();}
        },
        {
            listener: self.submitresults, 
            EventNames: 'click', 
            Handler: self.getwords
        }
    ];

    self.OnStimulusTimeOut = self.getwords


    return self;

}

