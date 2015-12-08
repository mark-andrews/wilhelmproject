/*
 * When we use the birtday picker from bday-picker.js, we use this to initialize it.
 */

var bday_picker_initialize = function(defaultDateString){

    $("#bday").birthdaypicker({
        maxAge: 80,
        minAge: 18,
        placeholder: false,
        defaultDate: defaultDateString
    });

    $(".birth-year").wrap("<div class='col-xs-4'></div>");
    $(".birth-month").wrap("<div class='col-xs-4'></div>");
    $(".birth-day").wrap("<div class='col-xs-4'></div>");

}
