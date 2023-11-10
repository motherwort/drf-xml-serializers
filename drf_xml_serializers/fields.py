import copy
import inspect
from collections import OrderedDict
from collections.abc import Mapping

import lxml.objectify
from django.core.validators import (
    MaxLengthValidator,
    MaxValueValidator,
    MinLengthValidator,
    MinValueValidator,
    ProhibitNullCharactersValidator,
)
from django.utils.translation import gettext_lazy as _
from rest_framework import fields as drf_fields
from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty
from rest_framework.utils.formatting import lazy_format
from rest_framework.validators import ProhibitSurrogateCharactersValidator


class Field(drf_fields.Field):
    default_error_messages = {
        "required": _("This field is required."),
        "null": _("This field may not be null."),
        "got_many": "Expected one value, got many",
    }

    def __init__(
        self,
        *,
        read_only=False,
        write_only=False,
        required=None,
        default=...,
        initial=...,
        source=None,
        label=None,
        help_text=None,
        style=None,
        error_messages=None,
        validators=None,
        allow_null=False,
        namespaces: dict[str, str] | None = None
    ):
        super().__init__(
            read_only=read_only,
            write_only=write_only,
            required=required,
            default=default,
            initial=initial,
            source=source,
            label=label,
            help_text=help_text,
            style=style,
            error_messages=error_messages,
            validators=validators,
            allow_null=allow_null,
        )
        self.namespaces = namespaces

    def get_value(self, element: lxml.objectify.ObjectifiedElement):
        values: list[lxml.objectify.ObjectifiedElement] | None = element.xpath(
            self.source, namespaces=self.namespaces
        )
        if values:
            if len(values) > 1:
                self.fail("got_many")
            return values[0]
        return empty

    def bind(self, field_name, parent):
        """
        Initializes the field name and parent for the field instance.
        Called when a field is added to the parent serializer instance.
        """

        self.field_name = field_name
        self.parent = parent

        # `self.label` should default to being based on the field name.
        if self.label is None:
            self.label = field_name.replace("_", " ").capitalize()

        # self.source should default to being the same as the field name.
        if self.source is None:
            self.source = field_name

        # self.source_attrs is a list of attributes that need to be looked up
        # when serializing the instance, or populating the validated data.
        if self.source == "*":
            self.source_attrs = []
        else:
            self.source_attrs = [self.field_name]


class BooleanField(Field, drf_fields.BooleanField):
    def to_internal_value(self, data: lxml.objectify.ObjectifiedElement):
        return drf_fields.BooleanField.to_internal_value(self, data.text)

    def to_representation(self, value):
        return drf_fields.BooleanField.to_representation(self, value)


class CharField(Field, drf_fields.CharField):
    def __init__(self, **kwargs):
        self.allow_blank = kwargs.pop("allow_blank", False)
        self.trim_whitespace = kwargs.pop("trim_whitespace", True)
        self.max_length = kwargs.pop("max_length", None)
        self.min_length = kwargs.pop("min_length", None)
        super().__init__(**kwargs)
        if self.max_length is not None:
            message = lazy_format(
                self.error_messages["max_length"], max_length=self.max_length
            )
            self.validators.append(MaxLengthValidator(self.max_length, message=message))
        if self.min_length is not None:
            message = lazy_format(
                self.error_messages["min_length"], min_length=self.min_length
            )
            self.validators.append(MinLengthValidator(self.min_length, message=message))

        self.validators.append(ProhibitNullCharactersValidator())
        self.validators.append(ProhibitSurrogateCharactersValidator())

    def to_internal_value(self, data: lxml.objectify.ObjectifiedElement):
        return drf_fields.CharField.to_internal_value(self, data.text)

    def to_representation(self, value):
        return drf_fields.CharField.to_representation(self, value)


class UUIDField(Field, drf_fields.UUIDField):
    def __init__(self, **kwargs):
        self.uuid_format = kwargs.pop("format", "hex_verbose")
        if self.uuid_format not in self.valid_formats:
            raise ValueError(
                "Invalid format for uuid representation. "
                'Must be one of "{}"'.format('", "'.join(self.valid_formats))
            )
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        return drf_fields.UUIDField.to_internal_value(self, data.text)

    def to_representation(self, value):
        return drf_fields.UUIDField.to_representation(self, value)


class IntegerField(Field, drf_fields.IntegerField):
    def __init__(self, **kwargs):
        self.max_value = kwargs.pop("max_value", None)
        self.min_value = kwargs.pop("min_value", None)
        super().__init__(**kwargs)
        if self.max_value is not None:
            message = lazy_format(
                self.error_messages["max_value"], max_value=self.max_value
            )
            self.validators.append(MaxValueValidator(self.max_value, message=message))
        if self.min_value is not None:
            message = lazy_format(
                self.error_messages["min_value"], min_value=self.min_value
            )
            self.validators.append(MinValueValidator(self.min_value, message=message))

    def to_internal_value(self, data):
        return drf_fields.IntegerField.to_internal_value(self, data.text)

    def to_representation(self, value):
        return drf_fields.IntegerField.to_representation(self, value)


class FloatField(Field, drf_fields.FloatField):
    def __init__(self, **kwargs):
        self.max_value = kwargs.pop("max_value", None)
        self.min_value = kwargs.pop("min_value", None)
        super().__init__(**kwargs)
        if self.max_value is not None:
            message = lazy_format(
                self.error_messages["max_value"], max_value=self.max_value
            )
            self.validators.append(MaxValueValidator(self.max_value, message=message))
        if self.min_value is not None:
            message = lazy_format(
                self.error_messages["min_value"], min_value=self.min_value
            )
            self.validators.append(MinValueValidator(self.min_value, message=message))

    def to_internal_value(self, data):
        return drf_fields.FloatField.to_internal_value(self, data.text)

    def to_representation(self, value):
        return drf_fields.FloatField.to_representation(self, value)


class _UnvalidatedField(Field):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.allow_blank = True
        self.allow_null = True

    def to_internal_value(self, data):
        return data

    def to_representation(self, value):
        return value


class ListField(Field, drf_fields.ListField):
    child = _UnvalidatedField()

    def __init__(self, **kwargs):
        self.child = kwargs.pop("child", copy.deepcopy(self.child))
        self.allow_empty = kwargs.pop("allow_empty", True)
        self.max_length = kwargs.pop("max_length", None)
        self.min_length = kwargs.pop("min_length", None)

        assert not inspect.isclass(self.child), "`child` has not been instantiated."
        assert self.child.source is None, (
            "The `source` argument is not meaningful when applied to a `child=` field. "
            "Remove `source=` from the field declaration."
        )

        super().__init__(**kwargs)
        self.child.bind(field_name="", parent=self)
        if self.max_length is not None:
            message = lazy_format(
                self.error_messages["max_length"], max_length=self.max_length
            )
            self.validators.append(MaxLengthValidator(self.max_length, message=message))
        if self.min_length is not None:
            message = lazy_format(
                self.error_messages["min_length"], min_length=self.min_length
            )
            self.validators.append(MinLengthValidator(self.min_length, message=message))

    def get_value(self, element: lxml.objectify.ObjectifiedElement):
        values: list[lxml.objectify.ObjectifiedElement] | None = element.xpath(
            self.source, namespaces=self.namespaces
        )
        return values

    def to_internal_value(self, data):
        """
        List of dicts of native values <- List of dicts of primitive datatypes.
        """
        if isinstance(data, (str, Mapping)) or not hasattr(data, "__iter__"):
            self.fail("not_a_list", input_type=type(data).__name__)
        if not self.allow_empty and len(data) == 0:
            self.fail("empty")
        return self.run_child_validation(data)

    def to_representation(self, data):
        """
        List of object instances -> List of dicts of primitive datatypes.
        """
        return [
            self.child.to_representation(item) if item is not None else None
            for item in data
        ]

    def run_child_validation(self, data):
        result = []
        errors = OrderedDict()

        for idx, item in enumerate(data):
            try:
                result.append(self.child.run_validation(item))
            except ValidationError as e:
                errors[idx] = e.detail

        if not errors:
            return result
        raise ValidationError(errors)
