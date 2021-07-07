"""
Extension of WTFormsRenderer class to support names and id fields
"""

from flask_bootstrap.forms import WTFormsRenderer
from dominate import tags
from markupsafe import Markup
from wtforms import SubmitField


def render_vform(form, **kwargs):
    r = VerboseRenderer(**kwargs)
    return Markup(r.visit(form))


class VerboseRenderer(WTFormsRenderer):
    def __init__(self,
                 action='',
                 id=None,
                 method='post',
                 extra_classes=[],
                 role='form',
                 enctype=None):
        super().__init__(
            action='',
            id=None,
            method='post',
            extra_classes=[],
            role='form',
            enctype=None)

    def _wrapped_input(self, node,
                       type='text',
                       classes=['form-control'], **kwargs):

        wrap = self._get_wrap(node)
        wrap.add(tags.label(node.label.text, _for=node.id))
        wrap.add(tags.input(type=type, name=node.name, id=node.name,
                            _class=' '.join(classes), **kwargs))

        return wrap

    def visit_SubmitField(self, node):
        button = tags.button(node.label.text,
                             _class='btn btn-default',
                             type='submit',
                             id=node.name+"-btn",
                             name=node.name,
                             value=node.name)

        return button

    def visit_DropField(self, node):
        """
        Custom field to render Bootstrap dropdown in the same form
        as the rest of the upload buttons

        https://getbootstrap.com/docs/3.3/components/#dropdowns
        """
        button = tags.button(node.label.text,
                             _class="btn btn-default dropdown-toggle",
                             type="button",
                             id=node.name+"-dropbtn",
                             name=node.name,
                             value=node.name)

        # Need to add some hyphenated attributes

        button['data-toggle'] = "dropdown"
        button['aria-haspopup'] = "true"
        button['aria-expanded'] = "true"

        button.add(tags.span(_class="caret"))

        fieldlist = tags.ul(
            _class="dropdown-menu",
            id=node.label.text
        )

        fieldlist['aria-labelledby'] = node.name+"-dropbtn"

        drop = tags.div(
            _class='dropdown'
        )

        drop.add(button)
        drop.add(fieldlist)

        return drop


    def visit_ButtonField(self, node):
        """
        Buttons aren't technically fields but this is being added to document things
        a bit better than relying solely on JS manipulation
        """
        button = tags.button(node.label.text,
                             _class="btn btn-info",
                             type="button",
                             id=node.name+"-btn",
                             name=node.name,
                             value=node.name,
                             disabled="disabled")
        return button


class DropField(SubmitField):
    pass


class ButtonField(SubmitField):
    pass

