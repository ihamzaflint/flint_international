from odoo import fields
from operator import attrgetter


# fields.Field.block_negative = False
# fields.Field._description_block_negative = property(attrgetter('block_negative'))
# 
# 
def monkey_patch(cls):
    """ Return a method decorator to monkey-patch the given class. """

    def decorate(func):
        name = func.__name__
        func.super = getattr(cls, name, None)
        setattr(cls, name, func)
        return func

    return decorate


#
# 
# @monkey_patch(fields.MetaField)
# def __init__(cls, name, bases, attrs):
#     print("AAA")
#     super(fields.MetaField, cls).__init__(name, bases, attrs)
#     if not hasattr(cls, 'type'):
#         return
# 
#     if cls.type and cls.type not in fields.MetaField.by_type:
#         fields.MetaField.by_type[cls.type] = cls
# 
#     # compute class attributes to avoid calling dir() on fields
#     cls.related_attrs = []
#     cls.description_attrs = []
#     for attr in dir(cls):
#         if attr.startswith('_related_'):
#             cls.related_attrs.append((attr[9:], attr))
#         elif attr.startswith('_description_'):
#             cls.description_attrs.append((attr[13:], attr))
# 
# 
# @monkey_patch(fields.Field)
# def get_description(self, env):
#     """ Return a dictionary that describes the field ``self``. """
#     desc = {'type': self.type}
#     for attr, prop in self.description_attrs:
#         value = getattr(self, prop)
#         if callable(value):
#             value = value(env)
#         if value is not None:
#             desc[attr] = value
#
#     return desc


#
# @monkey_patch(fields.Field)
# def _get_attrs(self, model, name):
#     attrs = _get_attrs.super(self, model, name)
#     return attrs
Default = object()  # default value for __init__() methods

from odoo.fields import Integer as Integer
from odoo.fields import Char as Char

fields.Field.block_negative = False
fields.Field._description_block_negative = property(attrgetter('block_negative'))


fields.Field.prevent_zero = False
fields.Field._description_prevent_zero = property(attrgetter('prevent_zero'))

fields.Field.email = False
fields.Field._description_email = property(attrgetter('email'))


# @monkey_patch(fields.Field)
# def get_description(self, env):
#     """ Return a dictionary that describes the field ``self``. """
#     desc = {'type': self.type}
#     self.description_attrs.append(('block_negative', '_description_block_negative'))
#     self.description_attrs.append(('prevent_zero', '_description_prevent_zero'))
#     self.description_attrs.append(('email', '_description_email'))
#     for attr, prop in self.description_attrs:
#         value = getattr(self, prop)
#         if callable(value):
#             value = value(env)
#         if value is not None:
#             desc[attr] = value
#
#     return desc
