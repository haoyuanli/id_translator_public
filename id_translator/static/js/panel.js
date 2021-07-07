//Scripts for information panel

$(function(){

    var base = getBaseUrl();

    $('#db-info').css("margin-top", $('.jumbotron').css("margin-top"))
    console.log()
//    $('#nav-alert').css("margin-left", $('.navbar-nav').position().left)


    $(document).ajaxStart(function ()
        {
        $('body').addClass('wait');

        }).ajaxComplete(function () {

        $('body').removeClass('wait');

    });

    $.ajax({
        type: "GET",
        url: base+"/get_panel_info",
        success: function(data) {

            for (var i in data) {
                var line = document.createElement("li")
                $(line).attr({class: "list-group-item"})
                $(line).text(i+" : "+data[i])
                $("#panel-list").append(line)
            }

        },

        error: function(err, status) {
            console.log(err)
            $(document).trigger("clear-alerts");
            $(document).trigger("set-alert-id-nav-alert", [
                {
                "message": err.responseText,
                "priority": 'error'
                }
            ]);

        }


    });
});


function getBaseUrl() {
    return window.location.href.match(/^.*\//);
}
