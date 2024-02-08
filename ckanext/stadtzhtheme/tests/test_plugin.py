import pytest
from ckan.lib.helpers import url_for
from ckan.tests import factories

import ckanext.stadtzhtheme.plugin as plugin


@pytest.mark.ckan_config("ckan.plugins", "stadtzhtheme showcase")
@pytest.mark.usefixtures("with_plugins")
class TestPlugin(object):
    def test_descr_file(self):
        theme_plugin = plugin.StadtzhThemePlugin()

        expected_keys = [
            "zip",
            "wms",
            "wmts",
            "wfs",
            "kml",
            "kmz",
            "json",
            "csv",
            "gpkg",
        ]
        descr = theme_plugin.descr_config
        assert all(k in descr.keys() for k in expected_keys), "Keys: %s" % descr.keys()

    def test_resource_description_value(self):
        theme_plugin = plugin.StadtzhThemePlugin()
        res = {"format": "CSV", "description": "My super CSV"}
        assert theme_plugin.get_resource_descriptions(res) == ["My super CSV"]

    def test_resource_description_file(self):
        theme_plugin = plugin.StadtzhThemePlugin()
        res = {"format": "CSV", "description": ""}

        descr = theme_plugin.get_resource_descriptions(res)

        assert len(descr) == 2
        assert descr[0] == "Comma-Separated Values."
        assert (
            descr[1]
            == "Weitere Informationen zu CSV finden Sie in unserer Rubrik Werkstatt "
            "unter [Informationen zu Datenformaten.]"
            "(https://www.stadt-zuerich.ch/portal/de/index/ogd/werkstatt/csv.html)"
        )

    def test_translations_without_orgs(self, app):
        dataset = factories.Dataset()

        url = url_for("dataset.read", id=dataset["name"])
        response = app.get(url).body

        assert "Aktualisierungs&shy;datum" in response, response
        assert "Date last updated" not in response, response

    def test_translations_with_org(self, app):
        org = factories.Organization()
        dataset = factories.Dataset(owner_org=org["id"])

        url = url_for("dataset.read", id=dataset["name"])
        response = app.get(url).body

        assert "Aktualisierungs&shy;datum" in response, response
        assert "Date last updated" not in response, response

    def test_translation_with_en_locale(self, app):
        org = factories.Organization()
        dataset = factories.Dataset(owner_org=org["id"])

        url = url_for("dataset.read", id=dataset["name"], locale="en")
        response = app.get(url).body

        assert "Aktualisierungs&shy;datum" not in response, response
        assert "Date last updated" in response, response
