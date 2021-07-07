"""
Handler to manage keycloak connection and auth methods
"""

import requests

import jwt
from jwt.algorithms import RSAAlgorithm
from keycloak import KeycloakOpenID


class KeycloakHandler:
    """
    Configs is the parsed keycloak configuration dictionary created on runtime
    in __main__
    """

    def __init__(self, configs):
        self.configs = configs
        self.conn = self.connect_to_keycloak()
        self.key_set = self.get_key_set()
        self.public_key = RSAAlgorithm.from_jwk(self.key_set)

    def connect_to_keycloak(self):
        """
        Establish connection to keycloak server
        """
        keycloak_openid = KeycloakOpenID(server_url=self.configs['KC_SERVER'] + "/auth/",
                                         client_id=self.configs['OIDC_CLIENT'],
                                         realm_name=self.configs['KC_REALM'],
                                         client_secret_key=self.configs['OIDC_CLIENT_SECRET'],
                                         verify=True)
        return keycloak_openid

    def get_key_set(self):
        """
        Obtain the JSON web key set from keycloak and replace ' with "
        """
        key_response = requests.get(self.conn.well_know()['jwks_uri'])
        key_set = str(key_response.json()['keys'][0]).replace("'", "\"")

        return key_set

    def decode_token(self, token):
        """
        Decode token using RS256
        """
        try:
            decoded = jwt.decode(token,
                                 self.public_key,
                                 audience=self.configs['OIDC_AUDIENCE'],
                                 algorithms=['RS256'])
            return {"roles": decoded['realm_access']['roles'],
                    "user": decoded['preferred_username']}
        except jwt.ExpiredSignatureError:
            return jwt.ExpiredSignature
        except jwt.DecodeError:
            return jwt.DecodeError
