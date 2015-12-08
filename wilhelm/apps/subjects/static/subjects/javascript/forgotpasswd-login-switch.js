$(document).ready(function() {
$('.forgotPwd-or-login').click(function(e) {
    e.preventDefault();
    $('#member-login').toggle('500');
    $('#forgot-my-password').toggle('500');
});
});
