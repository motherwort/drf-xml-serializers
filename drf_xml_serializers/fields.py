import lxml.objectify
from rest_framework import fields as drf_fields
from rest_framework.fields import ValidationError  # noqa
from rest_framework.fields import empty


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
        values: list[lxml.objectify.ObjectifiedElement] | None = element.xpath(
            self.xpath, namespaces=self.namespaces
        )
        if not values:
            return empty
        if len(values) > 1:
            self.fail("got_many")
        return values[0]


class BooleanXPathField(drf_fields.BooleanField, XPathField):
    pass


class CharXPathField(drf_fields.CharField, XPathField):
    def to_internal_value(self, data):
        if isinstance(data, lxml.objectify.StringElement):
            data = str(data)
        return super().to_internal_value(data)


class UUIDXPathField(drf_fields.UUIDField, XPathField):
    def to_internal_value(self, data):
        if isinstance(data, lxml.objectify.StringElement):
            data = str(data)
        if isinstance(data, lxml.objectify.IntElement):
            data = int(data)
        return super().to_internal_value(data)


class IntegerXPathField(drf_fields.IntegerField, XPathField):
    pass


class FloatXPathField(drf_fields.FloatField, XPathField):
    pass


class _UnvalidatedField(drf_fields._UnvalidatedField, XPathField):
    pass


class ListXPathField(drf_fields.ListField, XPathField):
    child = _UnvalidatedField()

    def get_value(self, element: lxml.objectify.ObjectifiedElement):
        values: list[lxml.objectify.ObjectifiedElement] | None = element.xpath(
            self.xpath, namespaces=self.namespaces
        )
        return values
