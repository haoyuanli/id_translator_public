# ID-translator
A lightweight tool for maintaining the various identifiers of patients in multiple studies. This 
tool provides two utilities for use:
1. REST API which can be used to query information about patients.
2. Web based GUI allowing authorized users complete editing access over patient records.

## Project Requirements
* Python 3.7.2
* MongoDB v4.0.7
* Nginx 1.12.2
* Keycloak


### Project Setup

Clone the repo and use the main branch.

Create a virtual environment to run the project.

    virtualenv id_environment

    source id_environment/bin/activate

    pip install -r requirements.txt

    pip install connexion[swagger-ui]
    
### Config Details
The configuration file used by the ID-translator has three main components corresponding to MongoDB, Keycloak
and input data.

    "mongo": {
        "URI": <MongoDB Location>,
        "DB": <Database Name>,
        "COLLECTION_MAIN": <Primary Database>,
        "COLLECTION_TEMP": <GSC Use Only>,
        "COLLECTION_LINK": <GSC use Only>,
        "SSL": <"True" if using SSL>,
        "CERT": <Location>
    }
If the MongoDB requires SSL, a string "True" should be used in the SSL key.

The configuration lists three collections, but the temp and link collections can be left blank when running
the ID-translator in --no-gsc mode (or by setting the default to --no-gsc). 

In the GSC mode, data normally uploaded to be used by the ID-translator is assumed to not have a primary key
and is stored in the temp collection. The link collection is used to store data uploaded through the /api 
endpoints which are meant to contain key pairs linking data in the temp collection to a primary key.
    
    "keycloak": {
        "KC_SERVER": <Server Location>,
        "KC_REALM": <Realm Name>,
        "OIDC_PROVIDER": "{}/auth/realms/{}",
        "OIDC_CLIENT": <Client>,
        "OIDC_AUDIENCE": <Audience>,
        "OIDC_CLIENT_SECRET": <Secret Key>,
        "OIDC_AUTHZ_ENDPOINT": "{}/auth/realms/{}/protocol/openid-connect/auth",
        "OIDC_TOKEN_ENDPOINT": "{}/auth/realms/{}/protocol/openid-connect/token",
        "OIDC_TOKEN_REV_ENDPOINT": "{}/auth/realms/{}/protocol/protocol/openid-connect/token/introspect",
        "OIDC_USERINFO_ENDPOINT": "{}/auth/realms/{}/protocol/protocol/openid-connect/userinfo",
        "FORMAT_ENDPOINTS": [
            "OIDC_PROVIDER", "OIDC_AUTHZ_ENDPOINT",
            "OIDC_TOKEN_ENDPOINT", "OIDC_TOKEN_REV_ENDPOINT", "OIDC_USERINFO_ENDPOINT"
        ]
    }

The keycloak details are standard information. The ID-translator validates tokens in the backend rather than
redirecting to a login page.

    "project": {
        "IDS_TO_RETURN": [<List of IDs to be included in Translation>],
        "PRIMARY_KEY": <PK>
    }

The IDS_TO_RETURN field is what determines which projects are returned by the ID-translator when the translate function
is called. The primary key is what is used when searching for records in the editor.

### Keycloak Details

Authentication and authorization through Keycloak is done by using realm roles. By default two roles are 
used to control access.

`id_edit` enables a user with this role to use the editor.

`id_upload` enables a user with this role to send POST requests to the REST endpoints.

These two roles need to be created in the Keycloak server for the appropriate realm specified 
in the configuration file.

### Features

The ID-translator has three main pages when using it in a web browser.

/translate opens the main feature, ID translation, which allows the searching
of any specified ID and will return any other IDs associated with it. This route is
also able to recieve GET requests if an ID is specified via /translate/<ID>

/editor opens a web editor which allows adding, deleting and modifying information
of any documents within the primary collection. These documents are searchable via
the primary key specified in the config.

/upload opens a file uploader which looks at any files stored within the data folder
of this application. In both operation modes, uploading a file through this page will
cause the primary collection to be updated. However, in the GSC mode, the temp collection
will first be updated and then any documents that also have a match within the link
collection will be synced up and uploaded into the primary collection.


### Running the System

Use `python -m id_translator --<optional args>` for the werkzeug development server through Flask.

The wsgi.py file is used to let uwsgi serve the ID-translator and ultimately 
allow Nginx to serve it up. You can test that uwsgi is able to serve the application
by using either:

`uwsgi ID-translator.ini` which will run the server locally

`uwsgi --ini ID-translator.ini --http {IP}:{Port}` to specify an IP and Port #

The ID-translator.ini file is used to configure uwsgi and results in a socket being created.
This socket needs to be specified in the nginx.conf file.

Be sure to change the permissions of the .socket that gets created so that the Nginx user
can execute it.

Once uwsgi is running, Nginx should be able to connect to it and serve the ID-translator.

#### Brief Nginx Setup

If you need the instance running as a non nginx/apache user follow this: https://wiki.apache.org/httpd/NonRootPortBinding Was needed for us due
to our filer system.
1. yum install nginx.x86_64
2. vi /etc/nginx/nginx.conf
3. Inside the http{} block add the following  
server {  
&nbsp;&nbsp;&nbsp;&nbsp;listen PortNumber ;  
&nbsp;&nbsp;&nbsp;&nbsp;listen [::]: PortNumber ;  
&nbsp;&nbsp;&nbsp;&nbsp;server_name ServerName ;  
&nbsp;&nbsp;&nbsp;&nbsp;root PathToFiles ;  
&nbsp;&nbsp;&nbsp;&nbsp;include /etc/nginx/default.d/*.conf;  
&nbsp;&nbsp;&nbsp;&nbsp;location / {  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;include uwsgi_params;  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;uwsgi_pass PathTo .Sock File ;  
&nbsp;&nbsp;&nbsp;&nbsp;}  
}  
#####Example:  
server {  
&nbsp;&nbsp;&nbsp;&nbsp;listen 8008;  
&nbsp;&nbsp;&nbsp;&nbsp;listen [::]:8008;  
&nbsp;&nbsp;&nbsp;&nbsp;server_name ga4gh02.bcgsc.ca;  
&nbsp;&nbsp;&nbsp;&nbsp;root /srv/idtranslator/ID-translator/;  
&nbsp;&nbsp;&nbsp;&nbsp;include /etc/nginx/default.d/*.conf;  
&nbsp;&nbsp;&nbsp;&nbsp;location / {  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;include uwsgi_params;  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;uwsgi_pass unix:/srv/idtranslator/ID-translator/idtranslator.sock;  
&nbsp;&nbsp;&nbsp;&nbsp;}  
}
4. Check the pathToFiles, ensure that the files are readable by the user that is running the nginx instance or you will see forbidden when
viewing the site in browser
5. Start the nginx instance, check and see if it can be viewed in browser


#### Authors
This application was implemented by Dashaylan Naidoo and Zoltan Bozoky.




