
$(function(){

    var base = getBaseUrl();
    var selected;

    $('#missing-btn').remove();


    // https://vitalets.github.io/x-editable/docs.html#editable

    $.ajax({
            type: "GET",
            url: base+"/get_uploads",
            success: function(message, status){
                for (var index in message) {
                    var entry = "<li class=\"list-group-item\"><a href=\"#\">"+message[index].text+"</a></li>"

                    $('#Documents').append(entry)
                    console.log(index)
                    console.log(entry)
                }

                $('#upload_confirm-btn').attr({disabled: "disabled"})


            },
            error: function(err){
                $(document).trigger("set-alert-id-feedback-alert", [
                {
                "message": err,
                "priority": 'error'
                }
                ]);
            }

    });

    $('#Documents').on("click", "li", function(e) {
        e.preventDefault();
        $(document).trigger("clear-alerts");
        selected = e.target.innerText;
        $(document).trigger("set-alert-id-permanent-alert", [
        {
        "message": "<b>"+selected+"</b> Ready for uploading!",
        "priority": 'info'
        }
        ]);
        // Hiding the X button for the alert to treat
        $(".close").attr({hidden: ""})
        $('#upload_confirm-btn').removeAttr("disabled")

    });

    $('#upload_confirm-btn').on("click", function(e) {
        e.preventDefault();
        upload_path = base+"/upload";
        var file = {"upload_confirm": selected};
        $.ajax({
            type: "POST",
            url: upload_path,
            data: file,
            success: function(message, status, xhr) {
                $(document).trigger("clear-alerts");
                if (xhr.status == 206){
                    console.log(typeof message)
                    $(document).trigger("set-alert-id-permanent-alert", [
                    {
                    "message": message.missed,
                    "priority": 'warning'
                    }
                    ]);



                } else {

                    $(document).trigger("set-alert-id-feedback-alert", [
                    {
                    "message": selected+" successfully uploaded!",
                    "priority": 'success'
                    }
                    ]);
                }

            },
            error: function(err, status) {
                $(document).trigger("clear-alerts");
                $(document).trigger("set-alert-id-feedback-alert", [
                {
                "message": err.responseText,
                "priority": 'error'
                }
                ]);
            }


        });

    });





});

function getBaseUrl() {
    return window.location.href.match(/^.*\//);
}
