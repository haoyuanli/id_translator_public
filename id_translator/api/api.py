#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
API endpoints (non GUI) for ID Translator, primary use case for GSC BioApps to upload syncing data
"""

import json

from flask import Blueprint, request, Response, current_app
from keycloak import exceptions


api = Blueprint('api', 'api', url_prefix='/api')

app = current_app

"""
Accessing handlers through the Flask app's config dict is a hacky way to access context specific
things within Blueprints
"""


@api.route('/session', methods=['POST'])
def api_create_session():
    """
    Entry endpoint for keycloak authentication.

    Payload should be a JSON struct:

    {
     "username" : <your_username>,
     "password" : <your_password>,
    }

    :return:
    """
    if request.method == 'POST':
        data = request.json
        try:
            token = app.config["KeycloakHandler"].conn.token(data["username"], data["password"])

        except exceptions.KeycloakAuthenticationError as KAE:
            message = str(KAE.error_message, 'utf-8')
            description = json.loads(message)["error_description"]
            return Response("Authentication Error: {}".format(description), status=404)

        return Response(json.dumps(token['access_token']), status=200)


@api.route('/limsids', methods=['GET'])
def api_get_linked_ids():
    """
    Grab all the ids in the linked collection

    :return: <lims_pt_id:project_id> JSON dict
    """

    resp = app.config["MongoHandler"].get_current_linked_ids()

    return Response(resp,
                    mimetype='application/json',
                    status=200)


@api.route('/limsids', methods=['POST'])
def api_add_lims_ids():
    """
    :param body: Nested json structure containing data to upload

    {
    "data":
            {
            "<project_id1>": "<lims_pt_id1>",
            "<project_id2>" : "<lims_pt_id2>"
            }
    }


    :return: 200 on successful db update
             204 if no new updates from payload
             401 on authentication error
             404 on malformed requests
    """
    headers = request.headers
    data = request.data
    if request.method == 'POST' and data:
        data = data.replace(b"'", b'"')
        kp = json.loads(data)
        try:
            token = headers['X-Token']
        except KeyError:
            return Response("Missing 'X-Token' in Headers", status=404)

        decoded = app.config["KeycloakHandler"].decode_token(token)

        if "id_upload" in decoded["roles"]:
            updates = app.config["MongoHandler"].put_linked_data(kp["data"])
            if updates:
                return Response("Success",
                                mimetype='application/json',
                                status=200)
            else:
                return Response("No updates",
                                mimetype='application/json',
                                status=204)
        else:
            return Response(
                "Account <{}> does not have upload permissions".
                format(decoded["user"]),
                mimetype='application/json',
                status=401)
    else:
        return Response(
            "Invalid Submission, check request",
            mimetype='application/json',
            status=404
        )


@api.route('/missed', methods=['GET'])
def api_get_missed_records():
    """
    GET all the records remaining in temp collection
    These are all the records that don't have links

    :return: list of pog ids
    """

    if request.method == 'GET':

        pogs = app.config["MongoHandler"].get_missed_records()

        return Response(pogs,
                        mimetype='application/json',
                        status=200)


@api.route('/records', methods=['GET'])
def api_get_all_records():
    """
    GET all records in collection

    :return: JSON list of all primary IDs
    """

    if request.method == 'GET':

        records = app.config["MongoHandler"].get_records()

        resp = json.dumps(records)

        return Response(resp,
                        mimetype='application/json',
                        status=200)


@api.route('/records/<id_>', methods=['GET'])
def api_get_record(id_):
    """
    Using a primary ID, return all the fields for a patient

    :return: 200: Success, JSON dict of all fields for ID
             404: Miss
    """
    if request.method == 'GET':

        fields = {}

        if request.method == 'GET':
            fields = app.config["MongoHandler"].get_record(id_)

        if fields == '{}':
            status = 404
        else:
            status = 200

        return Response(fields,
                        mimetype='application/json',
                        status=status)


