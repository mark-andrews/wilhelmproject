$("#other_language_box").prop("disabled", true);

$("input:radio[name=native_language]").change(function () {

    var checkedValue = $(this).val();

    if (checkedValue == "other") {
        $("#other_language_box").prop("disabled", false);
    } else {
        $("#other_language_box").prop("disabled", true);
    }

});
