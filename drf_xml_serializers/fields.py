import lxml.objectify
from rest_framework import fields as drf_fields
from rest_framework.fields import ValidationError  # noqa
from rest_framework.fields import empty


def to_python(value: lxml.objectify.ObjectifiedDataElement):
    # order matters
    if isinstance(value, lxml.objectify.StringElement):
        return str(value)
    if isinstance(value, lxml.objectify.BoolElement):
        return bool(value)
    if isinstance(value, lxml.objectify.FloatElement):
        return float(value)
    if isinstance(value, lxml.objectify.NumberElement):
        return int(value)
    return value


def get_xpath_values(
    *,
    element: lxml.objectify.ObjectifiedElement,
    xpath: str,
    namespaces: dict | None = None
):
    values = element.xpath(xpath, namespaces=namespaces)
    if not values:
        return values
    return list(map(to_python, values))


class XPathField(drf_fields.Field):
    default_error_messages = {
        "got_many": "Expected one value, got many",
    }

    def __init__(
        self, *, xpath: str = None, namespaces: dict[str, str] | None = None, **kwargs
    ):
        self.xpath = xpath
        self.namespaces = namespaces
        super().__init__(**kwargs)

    def get_value(self, element: lxml.objectify.ObjectifiedElement):
        assert self.xpath is not None
        values = get_xpath_values(
            element=element, xpath=self.xpath, namespaces=self.namespaces
        )
        if not values:
            return empty
        if len(values) > 1:
            self.fail("got_many")
        return values[0]


class BooleanXPathField(drf_fields.BooleanField, XPathField):
    pass


class CharXPathField(drf_fields.CharField, XPathField):
    pass


class UUIDXPathField(drf_fields.UUIDField, XPathField):
    pass


class IntegerXPathField(drf_fields.IntegerField, XPathField):
    pass


class FloatXPathField(drf_fields.FloatField, XPathField):
    pass


class _UnvalidatedField(drf_fields._UnvalidatedField, XPathField):
    pass


class ListXPathField(drf_fields.ListField, XPathField):
    child = _UnvalidatedField()

    def get_value(self, element: lxml.objectify.ObjectifiedElement):
        return get_xpath_values(
            element=element, xpath=self.xpath, namespaces=self.namespaces
        )
