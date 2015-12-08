var make_keep_alive_object = function(gateway, 
                                      ping_uid, 
                                      keep_alive,
                                      inter_ping_interval) 
    {

    var keep_alive_object = {};

    keep_alive_object.type = 'POST';
    keep_alive_object.url = gateway;
    keep_alive_object.dataType = 'json';
    keep_alive_object.data = {};
    keep_alive_object.data.ping_uid = ping_uid;
    keep_alive_object.data.keep_alive = JSON.stringify(keep_alive);

    keep_alive_object.success = function(data){
            console.log('keep-alive handshake success.');
            // Close the dialog.
            $('#timeout-confirm-dialog').dialog('close');

            if (data.keep_alive) {
                console.log('server says keep alive');
                // Stop coundown.
                stop_countdown = true; // Set the global; stop the clock.
                // Pause and ping again.
                setTimeout(
                    function(){ping(gateway, ping_uid, inter_ping_interval)}, 
                    inter_ping_interval
                );
                }
             else if (!data.keep_alive) {
                console.log('server says do not keep alive');
                window.location.replace("/");
             }
    };

    keep_alive_object.error = function(data) {
            console.log('keep-alive ajax handshake failed');
    };

    return keep_alive_object;

}

timeout_dialog = function(gateway, ping_uid, inter_ping_interval){

    stop_countdown = false; // A global variable.
    var seconds_remaining = 10;

    var countdown = function (t) {
        if (!stop_countdown) {
                console.log('stop_countdown' + stop_countdown + ' ' + t);
                if (t >= 0) {
                    $('#timeout-countdown').hide().text(t--)
                    .fadeIn(0).delay(1000)
                    .fadeOut(0, function(){countdown(t);});
                } else {
                    $('#timeout-confirm-dialog').dialog('close');
                    $.ajax(make_keep_alive_object(gateway, ping_uid, false, inter_ping_interval));
                }
        }
    };

    var continue_experiment_session = function(){
                                      // We must tell the server to turn the keep alive signal on.
                                      $.ajax(
                                              make_keep_alive_object(
                                                  gateway, 
                                                  ping_uid, 
                                                  true, 
                                                  inter_ping_interval)
                                      );
                                      $('#timeout-confirm-dialog').dialog('close'); 
    }

    $("#timeout-confirm-dialog").dialog({
        closeText: false,
        modal: true,
        width: 'auto',
        title: 'Timeout.',
        height: 'auto',
        closeOnEscape: true,
        draggable: false,
        resizable: false,
        close: function(event, ui){console.log('Dialog box closed');
                                   continue_experiment_session();},
        buttons: [
        {
            text: 'Continue experiment now',
            click: function(){console.log('Clicked: "Continue Now"'); 
                              continue_experiment_session();},
        }
           ]
        });

    countdown(seconds_remaining);
}
    

ping = function(gateway, ping_uid, inter_ping_interval) {
        // Send an ajax get request to gateway.
        // If we get a keep alive signal, pause for inter_ping_interval
        // and then call this function again.
        // If we get a keep_alive = false, we call the timeout_dialog.
        
        $.ajax({
            type: 'GET',
            url:gateway,
            dataType: 'json',
            data: {'ping_uid': ping_uid},
            success: function(data) {
                console.log(data);
                //  
                if (data.keep_alive) {
                    setTimeout(
                        function(){ping(gateway, ping_uid, inter_ping_interval)}, 
                        inter_ping_interval
                    );
                } else 
                    {
                    // If we don't get a keep alive signal, we will raise a timeout countdown dialog.
                    timeout_dialog(gateway, ping_uid, inter_ping_interval);
                    }
            },
            failure: function(){
                setTimeout(
                 function(){ping(gateway, ping_uid, inter_ping_interval)}, 
                 inter_ping_interval
                 );
            }
        });   
}
