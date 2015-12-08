slide_hangup = function(ping_uid) {
    console.log('attempting send hangup signal');
    $.ajax({
        dataType: "json",
        type: "POST",
        url: '/hangup_nowplaying',
        data: {'ping_uid': ping_uid, 'is_hangup': true},
        success: function(data) {
            console.log('hangup signal handshake received.');
            console.log('attempting href');
                if (data.is_hangup) {
                    window.location.href = data.experiment_uri;
                };
            }
    });
    };

stay_or_go = function(next_playlist_action) {
    console.log('attempting send stay or go signal');
    $.ajax({
        dataType: "json",
        type: "POST",
        url: '/hangup_playlist',
        data: {'next_playlist_action': next_playlist_action},
        success: function(data) {
            console.log('stay or go handshake received.');
            console.log('attempting href');
                if (data.next_uri) {
                    window.location.href = data.next_uri;
                };
            }
    });
    };
