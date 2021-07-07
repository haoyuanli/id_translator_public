"""
Implementation of tables for /editor functionality using flask-table classes
"""

from flask_table import Table, Col, ButtonCol, LinkCol
from flask_table.html import element


class EditCol(Col):
    def __init__(self, name, attr=None, attr_list=None,
                 allow_sort=True, show=True,
                 th_html_attrs=None, td_html_attrs=None,
                 a_html_attrs=None, column_html_attrs=None):
        super(EditCol, self).__init__(name, attr=None, attr_list=None,
                                      allow_sort=True, show=True,
                                      th_html_attrs=None, td_html_attrs=None,
                                      column_html_attrs=None)

        column_html_attrs = column_html_attrs or {}
        self.a_html_attrs = column_html_attrs.copy()
        self.a_html_attrs.update(a_html_attrs or {})

    def td(self, item, attr):
        content = self.td_contents(item, self.get_attr_list(attr))
        return element(
            'td',
            content=self.a(content),
            escape_content=False,
            attrs=self.td_html_attrs)

    def a(self, content):
        self.a_html_attrs["id"] = content
        return element(
            'a',
            content=content,
            escape_content=False,
            attrs=self.a_html_attrs)


a_attrs = {
    "href": "#",
    "data-type": "text",
    "class": "editable editable-click",
    "id": ""
}

"""
Overriding this entire class because the regular ButtonCol class sets the button_attrs['type']
to submit within the td_contents() function
"""


class DeleteButtonCol(LinkCol):
    """Just the same a LinkCol, but creates an empty form which gets
    posted to the specified url.
    Eg:
    delete = ButtonCol('Delete', 'delete_fn', url_kwargs=dict(id='id'))
    When clicked, this will post to url_for('delete_fn', id=item.id).
    Can pass button_attrs to pass extra attributes to the button
    element.
    """

    def __init__(self, name, endpoint, attr=None, attr_list=None,
                 url_kwargs=None, button_attrs=None, form_attrs=None,
                 form_hidden_fields=None, **kwargs):
        super(DeleteButtonCol, self).__init__(
            name,
            endpoint,
            attr=attr,
            attr_list=attr_list,
            url_kwargs=url_kwargs, **kwargs)
        self.button_attrs = button_attrs or {}
        self.form_attrs = form_attrs or {}
        self.form_hidden_fields = form_hidden_fields or {}

    def td_contents(self, item, attr_list):
        button_attrs = dict(self.button_attrs)
        button = element(
            'button',
            attrs=button_attrs,
            content=self.text(item, attr_list),
        )

        return button


class EditTable(Table):
    classes = ["table"]

    project = EditCol('Project', th_html_attrs={"data-editable": "true"},
                      a_html_attrs=a_attrs)
    _id = EditCol('ID', th_html_attrs={"data-editable": "true"}, a_html_attrs=a_attrs)

    delete = DeleteButtonCol('Delete', 'operations.editor_delete',
                             button_attrs={"id": "delete-btn", "type": "button", "class": "btn btn-danger"})


class Item(object):
    def __init__(self, project, _id):
        self.project = project
        self._id = _id

    def get_pair(self):
        return self.project, self._id
