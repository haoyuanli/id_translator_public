"""
Methods to handle incoming requests - GSC version, uses gsc_handler

"""

import json
import sys
from flask import current_app, Blueprint, redirect, request, \
    url_for, render_template, Response, jsonify

from flask_login import login_user, login_required
from flask_bootstrap import __version__ as FLASK_BOOTSTRAP_VERSION
from flask_nav.elements import Navbar, View, Subgroup, Link, Text
from keycloak import exceptions
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, InvalidName

from id_translator.api.nav import nav, Alert
from id_translator.api.logging import apilog
from id_translator.forms.forms import AdminLoginForm, AdminToolsForm, \
    HomeForm, TranslateForm, EditorForm, UploadForm
from id_translator.auth.id_user import User
from id_translator.api.tables import EditTable, Item


operations = Blueprint('operations', 'operations', url_prefix='/')

APP = current_app

nav.register_element('frontend_top', Navbar(
    View('ID Translator', '.get_home'),
    Subgroup(
        'Docs',
        Link('CanDIG', 'https://candig.bcgsc.ca/'),
    ),
    Text('Using Flask-Bootstrap {}'.format(FLASK_BOOTSTRAP_VERSION)),
    Alert(alerts="alerts", ids="nav-alert"),
    ))



@apilog
@operations.route('/', methods=['GET', 'POST'])
@operations.route('/home', methods=['GET', 'POST'])
def get_home():
    """
    Landing Page

    """
    form = HomeForm()

    if form.validate_on_submit():
        if form.translate.data:
            return redirect(url_for('operations.translate'))
        if form.admin.data:
            return redirect(url_for('operations.admin_login'))
    return render_template('b_home.html', form=form)


@apilog
@operations.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    """
    Login Page to access Editor and Upload tools
    """
    form = AdminLoginForm()

    if form.back.data:
        return redirect(url_for('operations.get_home'))
    if form.validate_on_submit():
        try:
            token = APP.config["KeycloakHandler"].conn.token(form.username.data, form.password.data)
        except exceptions.KeycloakAuthenticationError:
            print("Invalid login")
            return render_template('b_login.html', form=form)
        else:
            user_info = APP.config["KeycloakHandler"].conn.userinfo(token['access_token'])
            user = User(form.username.data)
            if "id_edit" in user_info["Access_Permissions"]:
                login_user(user)
                return redirect(url_for('operations.admin_tools'))

    return render_template('b_login.html', form=form)


@apilog
@operations.route('/admin_tools', methods=['GET', 'POST'])
@login_required
def admin_tools():
    """
    Navigation page to access Editor and Upload tools
    """
    form = AdminToolsForm()
    if form.back.data:
        return redirect(url_for('operations.get_home'))
    if form.edit.data:
        return redirect(url_for('operations.editor'))
    if form.upload.data:
        return redirect(url_for('operations.upload'))
    return render_template('b_admin_tools.html', form=form)


@apilog
@operations.route('/editor', methods=['GET', 'POST'])
@login_required
def editor():
    """
    In browser GUI manipulator for Mongo records. Most buttons rely heavily
    on ../static/js/editor.js functions and supporting _helper functions
    defined below.

    Produces an editable table of a record searched up using the primary key
    defined in the configuration file. This table uses the X-editable library
    to allow each cell to be edited.

    Changes to the table are tracked as a copy of the record stored within the
    MongoHandler class until submission.

    """
    eform = EditorForm()
    uform = UploadForm()
    pkey = APP.config['project']['PRIMARY_KEY']

    table = None
    #APP.config["MongoHandler"].clear_local_temp_records()

    if eform.back.data:
        return redirect(url_for('operations.admin_tools'))
    if eform.editor_query.data and eform.validate_on_submit():
        record = APP.config["MongoHandler"].get_record(eform.editor_query.data)
        if record:
            APP.config["MongoHandler"].set_editing_record(record)
            APP.config["MongoHandler"].set_delete_record()
            items = [Item(k, v) for k, v in record.items()]
            table = EditTable(items, table_id="Editor")
        else:
            return Response("{} is not a primary key of this collection".
                            format(eform.editor_query.data),
                            mimetype="text/html",
                            status=404)

    return render_template('b_editor.html',
                           eform=eform,
                           uform=uform,
                           table=table,
                           pkey=pkey)


@apilog
@operations.route('/keycheck', methods=['GET', 'POST'])
def key_check():
    """
    Route accessed via AJAX calls to determine whether a
    search term is a valid primary key. Used by editor.js

    """
    search_id = request.form['search']

    if APP.config["MongoHandler"].get_record(search_id):
        return Response(status=200)

    return Response(status=404)


@apilog
@operations.route('/editor_helper', methods=['GET', 'POST'])
def editor_helper():
    """
    Helper function to allow proper editing and addition of new
    key-pairs/rows to the db document/table. When a new row is
    created, the value is only able to be added once the key has
    been assigned a value. This logic is handled in the editor.js
    and this function expects that input flow.

    New rows have incremented DOM ids following a '++Project_X, ++ID_X'
    scheme, where X is the nth newest row, tracked by editor.js

    """
    if APP.config["MongoHandler"].check_editing_record():
        record = APP.config["MongoHandler"].get_editing_record()
        form_dict = request.form
        edited = form_dict['value'].strip()
        edited = edited.replace(" ", "_")
        new_record = form_dict['name'].split("_")[0]

        if new_record == "++Project":
            """
            A new entry needs to be added into the existing record. Use the sibling to grab
            the corresponding value
            """
            record[edited] = form_dict['sibling']

        elif new_record == "++ID":
            """
            A new ID has been added. The javascript on the Editor page prevents this from being
            editable until the Project field has been filled out, so the only possibility is that
            a keypair using the new Project (sibling) is in the record.
            """
            try:
                record[form_dict['sibling']] = edited
            except KeyError:
                """
                This really should not happen.
                """
                raise KeyError
        else:
            try:
                value = record[form_dict['name']]
                """
                If the code reaches this point it means that the value being edited is the
                project name, not ID, so the previous record needs to be deleted and remade.
                """
                record.pop(form_dict['name'])
                record[edited] = value
            except KeyError:
                """
                If a KeyError happens at this point, it means the value of a key,value pair in the
                mongo record has been edited, so use the sibling to access the pair and update it.
                """
                try:
                    val = record[form_dict['sibling']]
                    record[form_dict['sibling']] = edited

                except KeyError:
                    """
                    This second KeyError shouldn't ever trigger unless something is going 
                    really wrong with the backend records.
                    """
                    APP.logger.warn(KeyError)
                    raise KeyError

        APP.config["MongoHandler"].set_editing_record(record)
        return Response(edited, status=200)
    return Response(status=400)


@apilog
@operations.route('/editor_upload', methods=['GET', 'POST'])
def editor_upload():
    """
    Any changes made to a table in the Editor page will only be applied
    to the actual MongoDB record once this function is called via AJAX.

    This function is tied to the 'Upload Changes' button in the page.
    """
    if APP.config["MongoHandler"].check_editing_record():
        primary = request.form[APP.config["project"]["PRIMARY_KEY"]]
        APP.config["MongoHandler"].set_record(primary)
        return Response(status=200)

    return Response(status=404)

@apilog
@operations.route('/editor_delete', methods=['GET', 'POST'])
def editor_delete():
    """
    Any deletions made to the table are tracked by a dictionary in the MongoHandler.
    These deletions will be applied once the editor_upload() function is called.
    """
    form_dict = request.form
    try:
        APP.config["MongoHandler"].add_to_delete(form_dict['project'], form_dict['id'])

    except KeyError:
        return Response("Invalid delete keys", status=404)

    return Response("Project: {} with ID: {} queued for deletion!".
                    format(form_dict['project'], form_dict['id']), status=200)


@apilog
@operations.route('/translate', methods=['GET', 'POST'])
def translate():
    """
    Route to display browser page for Translate. Buttons and form depend
    on ../static/js/translate.js.

    Any ID specified within  'IDS_TO_RETURN' are valid search IDs
    """
    form = TranslateForm()
    ids = APP.config['project']['IDS_TO_RETURN']
    translated = None

    if form.back.data:
        return redirect(url_for('operations.get_home'))

    if form.validate_on_submit():
        translated = APP.config["MongoHandler"].translate(form.query.data)

    return render_template('b_translate.html', form=form, ids=ids, translated=translated)


@operations.route('/translate/<_id>', methods=['GET'])
def api_translate(_id):
    """
    API endpoint of Translate function. Returns all translatable
    IDs of id_

    :param _id: string
    :return:
    """

    translated = APP.config["MongoHandler"].translate(_id)
    if translated:
        return jsonify(translated)

    return Response("ID not associated with any projects", mimetype="text/html", status=404)


@operations.route('/translate_helper', methods=['GET', 'POST'])
def translate_helper():
    """
    Helper function to be called via AJAX tied to 'Translate' button on page.
    Returns a table of the translated values rather than just the JSON output

    """

    term = request.form['query']

    translated = APP.config["MongoHandler"].translate(term)

    if translated:
        table = APP.config["MongoHandler"].make_translated_table(translated)

        if table:
            return Response(str(table.__html__()), status=200)

    return Response("{} is not a valid search key.".format(term), status=404)


@apilog
@operations.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """
    Route to upload page. Buttons and form utilize ../static/js/uploader_gsc.js
    to perform their roles, notably the 'Missed Records' button is an AJAX
    call to get_missed_table() below

    """
    form = UploadForm()
    whole_form = request.form

    table = None

    if form.back.data:
        return redirect(url_for('operations.admin_tools'))

    """
    Normally the upload_confirm button is a boolean field but
    for this page, the uploader_gsc.js is replacing the boolean 
    with the name of the file selected. However, as far as the
    python code cares, it's still a boolean so accessing the data
    from the .data field doesn't work.
    """
    if form.upload_confirm.data:

        try:
            filename = whole_form['upload_confirm']
            file_path = '{}/data/{}'.format(sys.path[0], filename)
            APP.config["MongoHandler"].update_temp_collection(file_path)
            missed, new = APP.config["MongoHandler"].update_main_collection()

            if missed:
                missed_msg = "{} records were unable to be uploaded due to missing "\
                             "{} links. Contact BioApps for details. Missed records "\
                             "are viewable below.".format(missed, APP.config['project']['PRIMARY_KEY'])

                updated_msg = "{} records were added to or updated in the database.".format(new)

                payload = json.dumps({"missed": missed_msg, "updated": updated_msg})

                return Response(response=payload, status=206, mimetype='application/json')
            return Response(status=200)

        except ConnectionFailure:
            return Response("Cannot Establish Connection to Database", status=500)
        except FileNotFoundError:
            return Response("File Not Found", status=404)

    return render_template('/b_upload_gsc.html', form=form, table=table)


@operations.route('/get_missed_table')
def get_missed_table():
    """
    Accessed via AJAX to display any missed entries not linked via
    a BioApps file

    """
    table = APP.config["MongoHandler"].get_missed_table()

    return Response(str(table.__html__()), status=200)

@apilog
@operations.route('/get_uploads')
def get_uploads():
    """
    Route called via AJAX to populate the dropdown menu in
    the Upload page
    """

    files = APP.config["MongoHandler"].get_upload_files()
    return jsonify(files)


@operations.route('/get_panel_info')
def get_panel_info():
    """
    Route called via AJAX to get data to populate the info
    panel next to the jumbotron in Translate, Editor and Upload
    """
    main_db = APP.config["MongoHandler"].get_main_db_count()
    primary = APP.config["project"]["PRIMARY_KEY"]
    projects = APP.config["project"]["IDS_TO_RETURN"]

    return jsonify({
        "Searchable Records": main_db,
        "Editor Search Key": primary,
        "Valid Translation IDs": projects
    })


@operations.route('/autocomplete_translate', methods=['GET'])
def autocomplete_translate():
    """
    Called by jQueryUI autocomplete widget in ../static/js/translate.js
    to assist in searching up valid terms for translation
    """

    terms = APP.config["MongoHandler"].get_partial_record(
        request.args['term'], all_fields=True)

    return jsonify(matched=terms)


@operations.route('/autocomplete_editor', methods=['GET'])
def autocomplete_editor():
    """
    Called by jQueryUI autocomplete widget in ../static/js/editor.js
    to assist in searching up valid primary keys
    """
    terms = APP.config["MongoHandler"].get_partial_record(
        request.args['term'], all_fields=False)

    return jsonify(matched=terms)


@operations.app_errorhandler(ServerSelectionTimeoutError)
@operations.app_errorhandler(InvalidName)
def handle_error(error):
    message = [str(x) for x in error.args]
    status_code = 500
    success = False
    response = {
        'success': success,
        'error': {
            'type': error.__class__.__name__,
            'message': message
        }
    }

    return jsonify(response), status_code
