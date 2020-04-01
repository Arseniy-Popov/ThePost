from django import template

register = template.Library()


@register.filter
def add_attributes(field, inputs):
    inputs = inputs.split("_&")
    attrs = {}
    for input in inputs:
        attr, val = input.split(":")
        attrs[attr] = val
    return field.as_widget(attrs=attrs)
