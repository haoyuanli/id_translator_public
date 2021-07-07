#!/usr/bin/env python3

"""
Driver program for service
"""

import sys
import os
import argparse
import logging
from pathlib import Path

import connexion
import pkg_resources
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_nav import register_renderer

from id_translator.api import parsing
from id_translator.api.api import api
from id_translator.api.nav import nav, BSWithAlert
from id_translator.api.overrides import render_vform
from id_translator.auth.id_user import User
import id_translator.auth.keycloak_handler as keycloak


def main(args=None):
    """
    Main Routine

    Parse all the args and configure dataset parsing
    """
    if args is None:
        args = sys.argv[1:]

    path = Path(os.path.realpath(__file__)).parents
    parser = argparse.ArgumentParser('Run ID-translator service')
    parser.add_argument('--port', default=8820)
    parser.add_argument('--host', default='10.9.220.108')
    parser.add_argument('--logfile', default="{}/log/idtranslator.log".format(path[1]))
    parser.add_argument('--loglevel', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'])
    parser.add_argument('--config', default="./configs/main_config.json")
    parser.add_argument('--gsc', dest='gsc', action='store_true')
    parser.add_argument('--no-gsc', dest='gsc', action='store_false')
    parser.set_defaults(gsc=True)

    # known args used to supply command line args to pytest without raising an error here
    args, _ = parser.parse_known_args()

    # Logging configuration

    log_handler = logging.FileHandler(args.logfile)
    numeric_loglevel = getattr(logging, args.loglevel.upper())
    log_handler.setLevel(numeric_loglevel)

    APP.app.logger.addHandler(log_handler)
    APP.app.logger.setLevel(numeric_loglevel)

    APP.app.config["self"] = "http://{}:{}".format(args.host, args.port)

    # Service Parse
    config_dict = parsing.get_config_dict(args.config, APP.app.logger)

    APP.app.config["mongo"] = config_dict["mongo"]
    APP.app.config["keycloak"] = config_dict["keycloak"]
    APP.app.config["project"] = config_dict["project"]

    APP.app.config['BOOTSTRAP_SERVE_LOCAL'] = True

    # Set up blueprints and db handler

    if args.gsc:
        from id_translator.database.gsc_handler import GSCHandler as Handler
        from id_translator.blueprints.operations_gsc import operations
        print("Using GSC Implementation\nBioApps Endpoints Enabled")
        APP.app.register_blueprint(api)

    else:
        print("Using Non-GSC Implementation")
        from id_translator.database.db_handler import DBHandler as Handler
        from id_translator.blueprints.operations_normal import operations

    with APP.app.app_context():
        APP.app.config["MongoHandler"] = Handler(APP.app.config["mongo"],
                                                 APP.app.config["project"],
                                                 APP.app.logger)
        APP.app.config["KeycloakHandler"] = keycloak.KeycloakHandler(APP.app.config["keycloak"])

    APP.app.register_blueprint(operations)

    return APP, args.port


def configure_app():
    """
    Set up base flask app from Connexion

    App pulled out as global variable to allow import into
    testing files to access application context
    """
    app = connexion.FlaskApp(__name__, server='tornado')

    api_def = pkg_resources.resource_filename('id_translator', 'api/idtranslator.yaml')

    api_def = "./api/idtranslator.yaml"

    app.add_api(api_def, strict_validation=True, validate_responses=True)

    app.app.secret_key = '%7@#n.0$['


    Bootstrap(app.app)
    register_renderer(app.app, 'alerts', BSWithAlert)
    nav.init_app(app.app)


    login_manager = LoginManager()
    login_manager.login_view = 'operations.admin_login'
    login_manager.init_app(app.app)

    app.app.jinja_env.filters['render_vform'] = render_vform

    @login_manager.user_loader
    def load_user(user_id):
        return User(user_id)

    return app


APP = configure_app()

APPLICATION, PORT = main()

# expose flask app for uwsgi

application = APPLICATION.app

if __name__ == '__main__':
    print("id_translator running at {}".format(APPLICATION.app.config["self"]))
    APPLICATION.run(port=PORT)
