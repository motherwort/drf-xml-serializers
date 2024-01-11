from collections import OrderedDict

import lxml.objectify
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers as drf_serializers
from rest_framework.exceptions import ValidationError
from rest_framework.settings import api_settings

# Note: We do the following so that users of the framework can use this style:
#
#     example_field = serializers.CharField(...)
#
# This helps keep the separation between model fields, form fields, and
# serializer fields more explicit.
from .fields import (  # NOQA # isort:skip
    BooleanXPathField,
    CharXPathField,
    XPathField,
    FloatXPathField,
    IntegerXPathField,
    UUIDXPathField,
    ListXPathField,
)

# Non-field imports, but public API
from rest_framework.fields import (  # NOQA # isort:skip
    SkipField,
    empty,
)

LIST_SERIALIZER_KWARGS = drf_serializers.LIST_SERIALIZER_KWARGS + (
    "xpath",
    "namespaces",
)


# There's some replication of `XPathField` here


class BaseXPathSerializer(drf_serializers.BaseSerializer):
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

    @classmethod
    def many_init(cls, *args, **kwargs):
        """
        A copy of `rest_framework.serializers.BaseSerializer.many_init`,
        but `drf_xml_serializers.serializers.ListXmlSerializer` is
        used by default as `list_serializer_class`
        """
        allow_empty = kwargs.pop("allow_empty", None)
        max_length = kwargs.pop("max_length", None)
        min_length = kwargs.pop("min_length", None)
        child_serializer = cls(*args, **kwargs)
        list_kwargs = {
            "child": child_serializer,
        }
        if allow_empty is not None:
            list_kwargs["allow_empty"] = allow_empty
        if max_length is not None:
            list_kwargs["max_length"] = max_length
        if min_length is not None:
            list_kwargs["min_length"] = min_length
        list_kwargs.update(
            {
                key: value
                for key, value in kwargs.items()
                if key in LIST_SERIALIZER_KWARGS
            }
        )
        meta = getattr(cls, "Meta", None)
        list_serializer_class = getattr(
            meta, "list_serializer_class", ListXPathSerializer
        )
        return list_serializer_class(*args, **list_kwargs)


class XPathSerializer(BaseXPathSerializer, drf_serializers.Serializer):
    def to_internal_value(self, data):
        """A copy of `rest_framework.serializers.Serializer.to_internal_value`,
        except that instead of checking if data is an instance of `collections.abc.Mapping`
        we check if data is an instance of `lxml.objectify.ObjectifiedElement`"""

        if not isinstance(data, lxml.objectify.ObjectifiedElement):
            message = self.error_messages["invalid"].format(
                datatype=type(data).__name__
            )
            raise drf_serializers.ValidationError(
                {api_settings.NON_FIELD_ERRORS_KEY: [message]}, code="invalid"
            )

        ret = OrderedDict()
        errors = OrderedDict()
        fields = self._writable_fields

        for field in fields:
            validate_method = getattr(self, "validate_" + field.field_name, None)
            primitive_value = field.get_value(data)
            try:
                validated_value = field.run_validation(primitive_value)
                if validate_method is not None:
                    validated_value = validate_method(validated_value)
            except ValidationError as exc:
                errors[field.field_name] = exc.detail
            except DjangoValidationError as exc:
                errors[field.field_name] = drf_serializers.get_error_detail(exc)
            except SkipField:
                pass
            else:
                drf_serializers.set_value(ret, field.source_attrs, validated_value)

        if errors:
            raise ValidationError(errors)

        return ret


class ListXPathSerializer(drf_serializers.ListSerializer, BaseXPathSerializer):
    def __init__(self, *args, **kwargs):
        xpath = kwargs.pop("xpath", None)
        assert xpath is not None, "`xpath` is a required argument."
        super().__init__(*args, **kwargs)
        self.xpath: str = xpath

    def get_value(self, element: lxml.objectify.ObjectifiedElement):
        assert self.xpath is not None
        values: list[lxml.objectify.ObjectifiedElement] | None = element.xpath(
            self.xpath, namespaces=self.namespaces
        )
        return values
