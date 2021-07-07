//Globals to track project/ID additions
var PROJECT_COUNT = 0;
var ID_COUNT = 0;

$(function(){

    //Until a better way is figured out to send values, the primarykey
    //will be a hidden field in the editor page in order to use it to
    //access the record.

    var PK = $('#primarykey').contents().filter(function(){
        return this.nodeType == 3;
    })[0].textContent;

    var PK_value = ''


    if ($('#Editor').length) {
       PK_value = $('#'+PK).parent().siblings().children()[0].textContent;
       var PK_delete = $('#'+PK).parent().siblings().children()[1];
    }


    // Disable the PK's field and value from being edited
    disable_primary($, PK, PK_value, PK_delete)

    var base = getBaseUrl()

    //defaults
    $.fn.editable.defaults.url = '/editor_helper';

    // https://vitalets.github.io/x-editable/docs.html#editable

    // Editing the fields and values will go through minor validation
    // server side but won't be saved until the 'Update Record' button
    // is pressed

    $('#Editor').on("click", "a", function(e) {
        e.preventDefault();

        var sib = $(this).parent().siblings().children()[0];
        var sibID = sib.textContent
        $(this).editable({
           type: 'text',
           pk: PK,
           name: $(this).attr('id'),
           params: function(params){
                var data = {};
                data['id'] = params.pk
                data['name'] = params.name;
                data['value'] = params.value;
                data['sibling'] = sibID;

                return data
           },
           success: function(response){
                console.log(response);
                $(this).editable('option', 'name', response);

                $(sib).removeAttr('hidden');
           },
           error: function(response){
                console.log(response)
           }

        });
    });

    /*
    Only the delete button is tied to the table. This function
    examines the other elements in the row of the delete button
    pressed and constructs a project:id key pair to send back to
    the server for deletion in the record.
    */

    $('#Editor').on("click", "#delete-btn", function(e){
        e.preventDefault();
        var delete_path = base + "/editor_delete";
        var siblings = $(this).parent().siblings().children().get();
        var row = $(this).parents("tr")

        var data = {
            project: siblings[0].id,
            id: siblings[1].id
        };

        $.ajax({
            type: "POST",
            url: delete_path,
            data: data,
            success: function(message){
                $(document).trigger("set-alert-id-edit-alert", [
                {
                "message": message,
                "priority": 'success'
                }
                ]);

                row.remove();

            },
            error: function(err){
                $(document).trigger("set-alert-id-edit-alert", [
                {
                "message": err,
                "priority": 'error'
                }
                ]);
            }

        });

    });

    $()


    // This calls a route to save all the current changes to Mongo

    $('#upload-btn').on("click", function(e) {
        e.preventDefault();
        var upload_path = base + "/editor_upload";
        var PK_pair = {};
        PK_pair[PK] = PK_value;
        $.post(upload_path, PK_pair, function() {
            $(document).trigger("set-alert-id-edit-alert", [
            {
                "message": "Record Updated",
                "priority": 'success'
            }
            ]);
            $('form').submit();
        });
    });

    // Search button sends a post request to check if the query is using a primary
    // key prior to submitting the form

    $('#editor_search-btn').on('click', function(e) {
        e.preventDefault();
        formArray = $('form').serializeArray()

        search_id = formArray[0].value
        var keycheck_path = base + "/keycheck";
        var search_term = {"search": search_id}
        $.ajax({
            type: "POST",
            url: keycheck_path,
            data: search_term,
            success: function(){
                $('form').submit();
            },
            error: function(){
                $(document).trigger("set-alert-id-edit-alert", [
                {
                "message": search_id+" is not a primary key!",
                "priority": 'error'
                }
                ]);
            }

        });

    });

    $('#editor_query').autocomplete({
        minLength: 3,
        source: function(request, response){
            $.ajax({
            url: base + '/autocomplete_editor',
            data: request,
            success: function(terms) {
                console.log(terms)
                response(terms.matched)
                }
            });
        }
    });

    $('#add-btn').on('click', function(e) {
        e.preventDefault();
        extend_table($);
    });

    $('#unlock-btn').on('click', function(e) {
        e.preventDefault();
        $(document).trigger("set-alert-id-edit-alert", [
        {
            "message": "Editing the primary key values may result in a loss of data!",
            "priority": 'danger'
        }
        ]);
        enable_primary($, PK, PK_value, PK_delete);
    });




});

function getBaseUrl() {
    return window.location.href.match(/^.*\//);
}

function disable_primary($, PK, PK_value, PK_delete) {
    td = $('#'+PK).parent();
    td.append($('#'+PK).clone().prop("id", "pk_clone"));
    $('#pk_clone').editable('option','disabled', true);
    $('#'+PK).prop("hidden", "hidden");

    td = $('#'+PK_value).parent();
    td.append($('#'+PK_value).clone().prop("id", "pk_val_clone"));
    $('#pk_val_clone').editable('option','disabled', true);
    $('#'+PK_value).prop("hidden", "hidden");

    $(PK_delete).prop("disabled", "disabled");



}

function enable_primary($, PK, PK_value, PK_delete) {
    td = $('#'+PK).parent();
    $('#pk_clone').prop("hidden", "hidden");
    $('#pk_val_clone').prop("hidden", "hidden");
    $('#'+PK).removeAttr('hidden');
    $('#'+PK_value).removeAttr('hidden');
    $(PK_delete).removeProp("disabled")



}

function extend_table($){
    var rows = $('#Editor').find('tbody').children();
    var copy = $(rows[0]).clone();
    var row = $(copy[0]).children().get();
    var new_row = document.createElement("tr");
    for (index in row){
        var child = $($(row[index]).children());

        if (index == 0) {
            child.text("New_Project_"+PROJECT_COUNT);
            child.attr({id:"++Project_"+PROJECT_COUNT});
            PROJECT_COUNT += 1;
        } else if (index == 1) {
            child.text("New_ID_"+ID_COUNT);
            child.attr({id:"++ID_"+ID_COUNT});
            //child.editable('option','disabled', true);
            child.attr({hidden: ""})
            ID_COUNT += 1;
        }


        console.log(index, row[index])
        $(new_row).append(row[index])

    };

    //console.log($(copy[0]).children().get())
    $('#Editor').find('tbody').append(new_row)

}
