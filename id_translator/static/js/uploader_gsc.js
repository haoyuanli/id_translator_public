
$(function(){

    var base = getBaseUrl();
    var selected;



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
                    "message": message.updated,
                    "priority": 'success'
                    }
                    ]);

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

                $('#missing-btn').removeAttr("disabled")
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

    $('#missing-btn').on("click", function(e) {
        e.preventDefault();
        $('#table-space').empty();
        table_path = base+"/get_missed_table"
        $.ajax({
            type: "GET",
            url: table_path,
            success: function(data){


                $('#table-space').append(data);
                $('#table-space').children().attr({class: "table table-hover table-bordered"})

                var height_limit = 295
                if ($('#table-space').height() < 295) {
                    console.log(height_limit)
                    height_limit = $('#table-space').height();
                    console.log(height_limit)
                }
                console.log(height_limit)
                $('#table-space').css({
                    "height": height_limit,
                    "overflow-y": "scroll",
                    "padding-right": 0
                });
            }

        });

    });




});

function getBaseUrl() {
    return window.location.href.match(/^.*\//);
}
