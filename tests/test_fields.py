from decimal import Decimal
from uuid import UUID

import lxml.objectify
import pytest

from drf_xml_serializers import fields

xml = lxml.objectify.fromstring(
    """<?xml version="1.0" encoding="UTF-8"?>
    <Товар>
        <Ид>a9104793-9174-11eb-972c-38607706b20d</Ид>
        <НомерВерсии>AAAAAAAAAAE=57978</НомерВерсии>
        <ПометкаУдаления>true</ПометкаУдаления>
        <Штрихкод/>
        <Артикул>1</Артикул>
        <Наименование>Кофе</Наименование>
        <БазоваяЕдиница>796</БазоваяЕдиница>
        <Группы>
            <Ид>ec50ae26-916a-11eb-972c-38607706b20d</Ид>
        </Группы>
        <Описание/>
        <СтавкиНалогов>
            <СтавкаНалога>
                <Наименование>НДС</Наименование>
                <Ставка>Без налога</Ставка>
            </СтавкаНалога>
            <СтавкаНалога>
                <Наименование>НДС</Наименование>
                <Ставка>Без налога</Ставка>
            </СтавкаНалога>
        </СтавкиНалогов>
        <Вес>0.12</Вес>
    </Товар>""".encode()
)


xml2 = lxml.objectify.fromstring(
    """<?xml version="1.0" encoding="UTF-8"?>
    <Товар xmlns="urn:1C.ru:commerceml_2">
        <Ид>a9104793-9174-11eb-972c-38607706b20d</Ид>
        <НомерВерсии>AAAAAAAAAAE=57978</НомерВерсии>
        <ПометкаУдаления>true</ПометкаУдаления>
        <Штрихкод/>
        <Артикул>1</Артикул>
        <Наименование>Кофе</Наименование>
        <БазоваяЕдиница>796</БазоваяЕдиница>
        <Группы>
            <Ид>ec50ae26-916a-11eb-972c-38607706b20d</Ид>
        </Группы>
        <Описание/>
        <СтавкиНалогов>
            <СтавкаНалога>
                <Наименование>НДС</Наименование>
                <Ставка>Без налога</Ставка>
            </СтавкаНалога>
            <СтавкаНалога>
                <Наименование>НДС</Наименование>
                <Ставка>Без налога</Ставка>
            </СтавкаНалога>
        </СтавкиНалогов>
        <Вес>0.12</Вес>
    </Товар>""".encode()
)


def test_get_value():
    field = fields.Field(source="/Товар")
    value = field.get_value(xml)
    assert isinstance(value, lxml.objectify.ObjectifiedElement)

    field = fields.Field(source="/НеТовар")
    value = field.get_value(xml)
    assert value is fields.empty

    field = fields.Field(source="/Товар/СтавкиНалогов/СтавкаНалога")
    with pytest.raises(fields.ValidationError):
        value = field.get_value(xml)

    field = fields.ListField(source="/Товар/СтавкиНалогов/СтавкаНалога")
    value = field.get_value(xml)

    field = fields.Field(source="/Товар")
    value = field.get_value(xml2)
    assert value is fields.empty

    field = fields.Field(source="/p:Товар", namespaces={"p": "urn:1C.ru:commerceml_2"})
    value = field.get_value(xml2)
    assert isinstance(value, lxml.objectify.ObjectifiedElement)


def test_boolean_field():
    field = fields.BooleanField(source="/Товар/ПометкаУдаления")
    value = field.get_value(xml)
    data = field.run_validation(value)
    assert isinstance(data, bool)
    assert data is True


def test_char_field():
    field = fields.CharField(source="/Товар/Наименование")
    value = field.get_value(xml)
    data = field.run_validation(value)
    assert isinstance(data, str)
    assert data == "Кофе"


def test_uuid_field():
    field = fields.UUIDField(source="/Товар/Ид")
    value = field.get_value(xml)
    data = field.run_validation(value)
    assert isinstance(data, UUID)
    assert data == UUID("a9104793-9174-11eb-972c-38607706b20d")


def test_integer_field():
    field = fields.IntegerField(source="/Товар/БазоваяЕдиница")
    value = field.get_value(xml)
    data = field.run_validation(value)
    assert isinstance(data, int)
    assert data == 796


def test_float_field():
    field = fields.FloatField(source="/Товар/Вес")
    value = field.get_value(xml)
    data = field.run_validation(value)
    assert isinstance(data, float)
    assert data == 0.12


def test_decimal_field():
    field = fields.DecimalField(source="/Товар/Вес", max_digits=3, decimal_places=2)
    value = field.get_value(xml)
    data = field.run_validation(value)
    assert isinstance(data, Decimal)
    assert data == Decimal("0.12")


def test_list_field():
    field = fields.ListField(child=fields.UUIDField(), source="/Товар/Группы/Ид")
    value = field.get_value(xml)
    data = field.run_validation(value)
    assert isinstance(data, list)
    assert isinstance(data[0], UUID)
    assert data == [UUID("ec50ae26-916a-11eb-972c-38607706b20d")]
