var Widget = function(settings) {

    var self = {};

    self.HeadTag = settings.HeadTag;
    self.gatewayurl = settings.gatewayurl;
    self.ping_uid = settings.ping_uid;

    self.StartBox = self.HeadTag.find('#StartBox');
    self.FinishBox = self.HeadTag.find('#FinishBox');
    self.FinishMsg = self.HeadTag.find('#FinishMsg');
    self.StimulusBox = self.HeadTag.find('#StimulusBox');
    self.StartButton = self.HeadTag.find('#StartButton');

    self.HeadTag.show();
    self.StartBox.hide();
    self.StimulusBox.hide();
    self.FinishBox.hide();

    // What element is the "tag" for stimulus display.
    // It should not be empty.
    self.StimulusTag = $({});

    // The name we will use for the custom queue.
    self.StimulusDisplayQueue = 'StimulusDisplayQueue';

    // Default timings for stimulus presentation.
    self.timings = {
         fadeInDuration: 1000,
         fadeOutDuration: 1000,
         stimulusDuration: 60000,
         isi: 3000
        };

    self.tic = 100; // resolution of countdown timer

    // Default UserEvents is empty.
    self.UserEvents = [];

    // An array to collect all responses.
    self.responses = [];

    self.TerminateStimulusDisplay = function(responses) {

        // Store responses
        self.responses.push(responses);

        // Disable user events.
        self.UnbindUserEvents();

        // Trigger next stimulus.
        self.StimulusDequeue();

    }

    self.BindUserEvents = function() {

        if (self.UserEvents.length > 0)
            {

            for (var i=0; i<self.UserEvents.length; i++) 
                {
                var ue = self.UserEvents[i];
                ue.listener.bind(ue.EventNames, ue.Handler);
                }

            }

    }

    self.UnbindUserEvents = function() {

        if (self.UserEvents.length > 0)
            {

            for (var i=0; i < self.UserEvents.length; i++) 
                {
                var ue = self.UserEvents[i];
                ue.listener.unbind(ue.EventNames, ue.Handler);
                }

            }

    }



    // Return time in milliseconds since the "epoch".
    self.timestamp = function() {
        return new Date().getTime();
    }

    // Turn on stimulus event listeners; set the stimulus timeout.
    self.WaitForUserEventOrTimeOut = function() {
        self.BindUserEvents();
        self.StimulusCountdown = setTimeout(self.OnStimulusTimeOut, self.timings.stimulusDuration);
    }
    
    // TODO (Mon 19 Jan 2015 15:04:54 GMT): This is obsolete, I think.
    // Add function f to the StimulusDisplayQueue 
    // self.PushToStimulusQueue = function(f)
    //    {
    //    self.StimulusTag.queue(self.StimulusDisplayQueue).unshift(f);
    //    }

    // Add function f to the StimulusDisplayQueue 
    self.AddToStimulusQueue = function(f)
        {
        self.StimulusTag.queue(self.StimulusDisplayQueue, f);
        }

    // The next i functions on the StimulusDisplayQueue are removed and executed.
    self.StimulusDequeue = function(i) 
        {
        self.StimulusTag.dequeue(self.StimulusDisplayQueue);

        if (i !== undefined) {
            if (--i > 0 &&
            self.StimulusTag.queue(self.StimulusDisplayQueue).length > 0)
                {
                self.StimulusDequeue(i);
                }
            }
        }

    // Called when IterateStimuli terminates.
    self._finish = function() {
        self.send_data();
    };

    // On click of start button, the display begins.    
    self.StartButton.click(
        function(){
            self.StartBox.fadeOut(self._start);
        }
    );

    // What to do when we click the start button.
    self._start = function() {
        self.StimulusBox.fadeIn(self.start);
        }


    self.start = function() { self.IterateStimuli(); };
    self.finish = function() {console.log('finish'); self.deactivate(); };

    self.activate = function() {
        $.ajax({
            dataType: "json",
            url: self.gatewayurl,
            data: {'ping_uid': self.ping_uid},
            success: function(data) {
   
                self.ParseJsonData(data);
                self.StartBox.show();

                }
        });

//        $.getJSON(self.gatewayurl, function(data) {
//   
//                self.ParseJsonData(data);
//                self.StartBox.show();
//
//                });
    };

    self.processfeedback = function(data) {}; // Empty function by default.

    self.deactivate = function() {
        console.log('deactivate');
        self.HeadTag.fadeOut(self.next_in_chain);
    };

    self.send_data = function(callback) {
        $.ajax({
            url: self.gatewayurl,
            type: 'POST',
            data: {'ping_uid': self.ping_uid,
                  'responses' : JSON.stringify(self.responses)
            },
            dataType: 'json'
            }).done(function(data) 
                {
                self.processfeedback(data);
                console.log('send_data done: got feedback.');
                self.StimulusBox.fadeOut(function()
                    {console.log('StimulusBox hide.');
                        self.FinishBox.fadeIn(self.finish);
                    });
                }
            ).fail(console.log('failed ajax'));
        };

    self.IterateStimuli = function()
        {
        // Iterate through the array "contents", sequentially assigning each
        // value to the text attribute of "StimulusTag", using the fadeIn, fadeOut,
        // delay and isi provided in the object literal "timings".
        // This is a recursive function.

        if (self.i == null) {
            self.i=0;
        }

        if (0 <= self.i && self.i < self.Stimuli.length) {

            self.AddToStimulusQueue(function() 
                {
                self.StimulusTag.hide(0, function(){self.StimulusDequeue();});
                }
            );

            self.AddToStimulusQueue(function()
                {
                self.DisplayStimulus(self.Stimuli[self.i]);
                }
            );

            self.AddToStimulusQueue(function()
                {
                self.StimulusTag.fadeIn(self.timings.fadeInDuration, function(){self.StimulusDequeue();});
                }
            );

            self.AddToStimulusQueue(function()
                {
                self.StimulusDisplayed = self.timestamp();
                self.StimulusDequeue();
                }
            );

            self.AddToStimulusQueue(function()
                {
                self.WaitForUserEventOrTimeOut();
                }
            );

            self.AddToStimulusQueue(function()
                {
                self.StimulusTag.fadeOut(self.timings.fadeOutDuration, _iterate);
                }
            );
       
            self.StimulusDequeue();

            }     
     
        function _iterate() {
            self.i++;
            setTimeout(
                function() {
                    if (self.i === self.Stimuli.length) 
                        {
                        self._finish(); // End of iteration.
                        }
                    else 
                        { 
                        self.IterateStimuli();
                        }
                }, self.timings.isi
                );

            }   

    }

    return self;

};


