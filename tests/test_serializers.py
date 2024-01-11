from uuid import UUID

import lxml.objectify

from drf_xml_serializers import serializers

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
        </СтавкиНалогов>
        <Вес>0.12</Вес>
    </Товар>""".encode()
)

xml2 = lxml.objectify.fromstring(
    """<?xml version="1.0" encoding="UTF-8"?>
<КоммерческаяИнформация ВерсияСхемы="2.10" ДатаФормирования="2023-05-17T16:06:18" Ид="1">
    <Каталог СодержитТолькоИзменения="true">
        <Ид>bb68bb30-5cb6-4235-85a6-52d66635a62e</Ид>
        <ИдКлассификатора>bb68bb30-5cb6-4235-85a6-52d66635a62e</ИдКлассификатора>
        <Наименование>Основной каталог товаров</Наименование>
        <Описание>Основной каталог товаров</Описание>
        <Число>1</Число>
        <БулевоИстина>true</БулевоИстина>
        <БулевоЛожь>false</БулевоЛожь>
    </Каталог>
    <Предложение>
        <Ид>a9104793-9174-11eb-972c-38607706b20d</Ид>
        <Объект>
            <Число>1</Число>
            <Объект>
                <Число>2</Число>
            </Объект>
        </Объект>
        <Цены>
            <Цена>
                <Представление>100 руб за шт</Представление>
                <ИдТипаЦены>5822ebda-96a7-11eb-805b-2cf05dea98c0</ИдТипаЦены>
                <ЦенаЗаЕдиницу>100</ЦенаЗаЕдиницу>
                <Валюта>руб</Валюта>
            </Цена>
            <Цена>
                <Представление>120 руб за шт</Представление>
                <ИдТипаЦены>9243451b-d222-49a3-b0f8-134cce762863</ИдТипаЦены>
                <ЦенаЗаЕдиницу>120</ЦенаЗаЕдиницу>
                <Валюта>руб</Валюта>
            </Цена>
        </Цены>
    </Предложение>
</КоммерческаяИнформация>""".encode()
)


def test_serializer_get_value():
    serializer = serializers.XPathSerializer(xpath="/Товар")
    value = serializer.get_value(xml)
    assert isinstance(value, lxml.objectify.ObjectifiedElement)


def test_serializer():
    class ProductSerializer(serializers.XPathSerializer):
        uuid = serializers.UUIDXPathField(xpath="Ид")
        group_uuids = serializers.ListXPathField(
            child=serializers.UUIDXPathField(), xpath="Группы/Ид"
        )

    serializer = ProductSerializer(xpath="/Товар", data=xml)
    serializer.is_valid()
    assert serializer.validated_data == {
        "uuid": UUID("a9104793-9174-11eb-972c-38607706b20d"),
        "group_uuids": [UUID("ec50ae26-916a-11eb-972c-38607706b20d")],
    }


def test_serializer_many():
    class PriceSerializer(serializers.XPathSerializer):
        value = serializers.IntegerXPathField(xpath="ЦенаЗаЕдиницу")

    class RootSerializer(serializers.XPathSerializer):
        prices = PriceSerializer(
            xpath="/КоммерческаяИнформация/Предложение/Цены/Цена", many=True
        )

    serializer = RootSerializer(data=xml2)

    serializer.is_valid()
    assert serializer.validated_data == {"prices": [{"value": 100}, {"value": 120}]}


xml3 = lxml.objectify.fromstring(
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
        </СтавкиНалогов>
        <Вес>0.12</Вес>
    </Товар>""".encode()
)


def test_serializer_with_namespace():
    ns = {"p": "urn:1C.ru:commerceml_2"}

    class ProductSerializer(serializers.XPathSerializer):
        uuid = serializers.UUIDXPathField(xpath="p:Ид", namespaces=ns)
        group_uuids = serializers.ListXPathField(
            child=serializers.UUIDXPathField(), xpath="p:Группы/p:Ид", namespaces=ns
        )

    serializer = ProductSerializer(xpath="/p:Товар", data=xml3, namespaces=ns)
    serializer.is_valid()
    assert serializer.validated_data == {
        "uuid": UUID("a9104793-9174-11eb-972c-38607706b20d"),
        "group_uuids": [UUID("ec50ae26-916a-11eb-972c-38607706b20d")],
    }
