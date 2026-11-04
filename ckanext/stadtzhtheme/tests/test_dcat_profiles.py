import pytest
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, XSD

from ckanext.stadtzhtheme.dcat.profiles import (
    DCAT,
    DCT,
    StadtzhSwissDcatProfile,
    parse_time_range,
)

DATASET_URI = URIRef("https://data.stadt-zuerich.ch/dataset/test-dataset")


@pytest.mark.parametrize(
    "time_range, expected",
    [
        ("2025", ("2025-01-01", "2025-12-31")),
        ("1800-2025", ("1800-01-01", "2025-12-31")),
        ("1993–2025", ("1993-01-01", "2025-12-31")),
        ("2006 - 2025", ("2006-01-01", "2025-12-31")),
        ("1977 – 2024", ("1977-01-01", "2024-12-31")),
        (" 2006 - 2025 ", ("2006-01-01", "2025-12-31")),
        ("01.08.2020 - 15.07.2030", ("2020-08-01", "2030-07-15")),
        ("01.08.2020 – 15.07.2030", ("2020-08-01", "2030-07-15")),
        ("01.08.2020-15.07.2030", ("2020-08-01", "2030-07-15")),
        ("1.1.2023 - 29.07.2023", ("2023-01-01", "2023-07-29")),
    ],
)
def test_parse_time_range_supported_formats(time_range, expected):
    assert parse_time_range(time_range) == {
        "start_date": expected[0],
        "end_date": expected[1],
    }


@pytest.mark.parametrize(
    "time_range",
    [
        None,
        "",
        "Laufende Nachführung",
        "30.09.2026",
        "22.04.2007 - aktuell",
        "01.01.2020 - gestern",
        "2012-heute",
        "ab 2023",
        "1992-01   – 2026-08",
        "1.1998 –  8.2026",
        "2021 bis 2024",
        "31/08/1939 - 30/09/2026",
        "31.02.2020 - 01.03.2020",
        "2025 - 2020",
        "01.01.2025 - 31.12.2020",
    ],
)
def test_parse_time_range_unsupported_formats(time_range):
    assert parse_time_range(time_range) is None


def _dataset_dict(**kwargs):
    dataset_dict = {
        "id": "abc-123",
        "name": "test-dataset",
        "title": "Test Dataset",
        "notes": "Description",
        "tags": [],
        "resources": [],
    }
    dataset_dict.update(kwargs)
    return dataset_dict


def _graph_from_dataset(dataset_dict):
    g = Graph()
    profile = StadtzhSwissDcatProfile(g)
    profile.graph_from_dataset(dataset_dict, DATASET_URI)
    return g


def test_graph_temporal():
    g = _graph_from_dataset(_dataset_dict(timeRange="1993 – 2025"))

    temporals = list(g.objects(DATASET_URI, DCT.temporal))
    assert len(temporals) == 1
    temporal = temporals[0]
    assert (temporal, RDF.type, DCT.PeriodOfTime) in g
    assert g.value(temporal, DCAT.startDate) == Literal("1993-01-01", datatype=XSD.date)
    assert g.value(temporal, DCAT.endDate) == Literal("2025-12-31", datatype=XSD.date)


def test_graph_temporal_unsupported_format():
    g = _graph_from_dataset(_dataset_dict(timeRange="Laufende Nachführung"))

    assert list(g.objects(DATASET_URI, DCT.temporal)) == []


def test_graph_temporal_from_extras():
    g = _graph_from_dataset(
        _dataset_dict(extras=[{"key": "timeRange", "value": "2006-2025"}])
    )

    assert len(list(g.objects(DATASET_URI, DCT.temporal))) == 1
