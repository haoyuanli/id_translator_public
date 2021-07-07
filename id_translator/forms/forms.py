from flask_wtf import FlaskForm
from wtforms.fields import *
from wtforms.validators import DataRequired
from id_translator.api.overrides import DropField, ButtonField


class AdminLoginForm(FlaskForm):
    username = StringField(u'Username', validators=[DataRequired()])
    password = PasswordField(u'Password', validators=[DataRequired()])
    login = SubmitField(u'Login')
    back = SubmitField(u'Back')


class HomeForm(FlaskForm):
    translate = SubmitField(u'ID Translation')
    admin = SubmitField(u'Admin Login')


class TranslateForm(FlaskForm):
    query = StringField(u'Pipeline ID', validators=[DataRequired()])
    translate = SubmitField(u'Translate')
    back = SubmitField(u'Back')


class AdminToolsForm(FlaskForm):
    edit = SubmitField(u'Editor')
    upload = SubmitField('Upload')
    back = SubmitField(u'Back')


class EditorForm(FlaskForm):
    editor_query = StringField(u'Query')
    editor_search = SubmitField(u'Search')
    back = SubmitField(u'Back')


class UploadForm(FlaskForm):
    drop = DropField(u'Documents')
    upload_confirm = SubmitField(u'Upload')
    back = SubmitField(u'Back')
    missing = ButtonField(u'Missed Records')

