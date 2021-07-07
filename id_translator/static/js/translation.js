$(function(){

    var base = getBaseUrl();

    $('#translate-btn').on("click", function(e){
        e.preventDefault();
        $(document).trigger("clear-alerts");
        $('#table-space').empty();
        var data = $('.form-control');
        console.log(data[0].value)
        $.ajax({
            type: "POST",
            url: base+"/translate_helper",
            data: data,
            success: function(translated) {
                $('#table-space').append(translated)
                $('#table-space').children().attr({class: "table table-bordered"})
            },
            error: function(err, status) {
                $(document).trigger("clear-alerts");
                $(document).trigger("set-alert-id-permanent-alert", [
                {
                "message": err.responseText,
                "priority": 'error'
                }
                ]);
            }


        });
    });



    $('#query').autocomplete({


        minLength: 3,
        source: function(request, response){
            $.ajax({
            url: base + '/autocomplete_translate',
            data: request,
            success: function(terms) {
                console.log(terms)
                response(terms.matched)
                }

            });

        }

    });




});

function getBaseUrl() {
    return window.location.href.match(/^.*\//);
}