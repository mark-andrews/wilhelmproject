var ANSWidgetObject = function(domtag, gatewayurl, ping_uid)
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
    self.canvas = self.StimulusTag.find('#stimulus_canvas')[0];
    self.StimulusTag.hide();

    self.context = self.canvas.getContext('2d');

    // Parse the incoming json data.
    self.ParseJsonData = function(data) {

        self.Stimuli = data.stimuli;
        self.StartButton.text(data.start_message);
        self.separation = data.separation;
        self.scale_factor = data.scale_factor;
        self.color = data.color;
        self.timings = {
             fadeInDuration: parseFloat(data.fadeInDuration) *1000,
             fadeOutDuration: parseFloat(data.fadeOutDuration) * 1000,
             stimulusDuration: parseFloat(data.timeOutDuration) * 1000, 
             isi: parseFloat(data.isi) * 1000
            };

        self.context.canvas.width = self.separation + self.scale_factor * 4;
        self.context.canvas.height = self.scale_factor * 2;

    }

    self.get_distances = function(click_coordinates, stimulus){

        display_left_center_x = stimulus.left.display_center[0];
        display_left_center_y = stimulus.left.display_center[1];

        display_right_center_x = stimulus.right.display_center[0];
        display_right_center_y = stimulus.right.display_center[1];

        return {
            left: euclidean_distance(click_coordinates, [display_left_center_x, display_left_center_y]),
            right: euclidean_distance(click_coordinates, [display_right_center_x, display_right_center_y])
        };
       
    }

    self.OnCanvasClick = function(e) {

        var responseTime = self.timestamp()
        var hit = false; // Did they click a dot display?

        // #############################################
        // Determine if they clicked within one or other
        // of the two dot displays.
        var rect = self.canvas.getBoundingClientRect();
        var clickedX = e.pageX - rect.left;
        var clickedY = e.pageY - rect.top;

        var distances = self.get_distances([clickedX, clickedY], 
                                            self.Stimuli[self.i]);

        if (distances.left <= self.scale_factor) {
            hit = true;
            dot_display_chosen = self.Stimuli[self.i].left.uid;
            console.log('left')
        }
        else if (distances.right <= self.scale_factor) {
            hit = true;
            dot_display_chosen = self.Stimuli[self.i].right.uid;
            console.log('right')
        } else {
            hit = false;
        }
        
        // ##########################################

        if (hit) {
            clearTimeout(self.StimulusCountdown); // Stop the timeout countdown

            // Assemble results as an object.
            var results = {
                order: self.i,
                stimulus_left: self.Stimuli[self.i].left.uid,
                stimulus_right: self.Stimuli[self.i].right.uid,
                response: dot_display_chosen,
                onset: self.StimulusDisplayed,
                responseTime: responseTime,
                latency: responseTime - self.StimulusDisplayed
            }

            self.TerminateStimulusDisplay(results);
       
        }

        };

    self.OnStimulusTimeOut = function() {
        
        // Assemble results as an object.
        var results = {
            order: self.i,
            stimulus_left: self.Stimuli[self.i].left.uid,
            stimulus_right: self.Stimuli[self.i].right.uid,
            response: null,
            onset: self.StimulusDisplayed,
            responseTime: null,
            latency: null
        }

        self.TerminateStimulusDisplay(results);

    };

    self.UserEvents = 
    [
        {
            listener: self.StimulusTag,
            EventNames: 'click',
            Handler: function(e) {self.OnCanvasClick(e)}
        }
    ];


    self.DrawDotDisplay = function(dot_display_object){

        var scale = dot_display_object.display_scale;
        var centerX = dot_display_object.display_center[0];
        var centerY = dot_display_object.display_center[1];
        var color = dot_display_object.display_color;

        for (i = 0; i < dot_display_object.number_of_circles; i++) {

              var center_x = centerX + scale*dot_display_object.circles[i][0];
              var center_y = centerY + scale*dot_display_object.circles[i][1];
              var radius = scale*dot_display_object.circles[i][2];

              self.context.beginPath();
              self.context.arc(center_x, center_y, radius, 0, 2 * Math.PI, false);
              self.context.fillStyle = self.color;
              self.context.fill();
              self.context.closePath();
        }

    }

    self.DisplayStimulus = function(stimulus) {

        console.log(stimulus);

        self.context.clearRect(0, 0, self.canvas.width, self.canvas.height);

        stimulus.left.display_center = [self.scale_factor, self.scale_factor];
        stimulus.left.display_scale = self.scale_factor;
        stimulus.left.display_color = self.display_color;

        stimulus.right.display_center = [self.separation + self.scale_factor * 3, self.scale_factor];
        stimulus.right.display_scale = self.scale_factor;
        stimulus.right.display_color = self.display_color;

        self.DrawDotDisplay(stimulus.left);
        self.DrawDotDisplay(stimulus.right);

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

var euclidean_distance = function(pointA, pointB){
    var sum_of_squares = Math.pow(pointA[0] - pointB[0], 2) + Math.pow(pointA[1] - pointB[1], 2);
    return Math.sqrt(sum_of_squares);
}
