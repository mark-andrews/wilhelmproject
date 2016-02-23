// From http://stackoverflow.com/a/2507043/1009979
function NotIsEmail(email) {
  var regex = /^([a-zA-Z0-9_.+-])+\@(([a-zA-Z0-9-])+\.)+([a-zA-Z0-9]{2,4})+$/;
  return !regex.test(email);
}


var process_signupform = function(minimal_password_length) {

    var firstname = $('input[name=firstname]').val().trim();
    var username_and_email = $('input[name=username]').val().trim();
    var password = $('input[name=password]').val();
    var confirmpassword = $('input[name=confirmpassword]').val();

    var valid = true;

    $('.firstname-live-error, .username-live-error, .password-live-error .check-password-live-error').text('').show();

    if (firstname == '') {
        $('.firstname-live-error').text('First name should not be empty.').show();
        valid = false;
    }

    if (username_and_email == '') {
        $('.username-live-error').text('Email address should not be empty.').show();
        valid = false;
    } else if (username_and_email.length > 30) {
        $('.username-live-error').text('Your email address should be less than 30 characters.').show();
        valid = false;
    } else if (NotIsEmail(username_and_email)) {
        $('.username-live-error').text('That email address does not look valid.').show();
        valid = false;
    }

    if (password.length < minimal_password_length) {
        var error_msg = "The password should be at least {0} characters.".format(minimal_password_length);
        $('.password-live-error').text(error_msg).show();
        valid = false;
    } else if (password !== confirmpassword) {
        $('.check-password-live-error').text('Passwords do not match.').show();
        valid = false;
    }

    return valid;
}

