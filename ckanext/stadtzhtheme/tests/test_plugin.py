import pytest
from ckan.lib.helpers import url_for
from ckan.tests import factories, helpers

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

    def test_markdown_snippet_value(self):
        resource_csv = factories.Resource(format="CSV", description="My super CSV")
        assert resource_csv.get("markdown_snippet")
        assert "renku" in resource_csv.get("markdown_snippet")
        assert "SQL" in resource_csv.get("markdown_snippet")
        assert resource_csv.get("package_id") in resource_csv.get("markdown_snippet")

        resource_parquet = factories.Resource(
            format="parquet", description="My super parquet"
        )
        assert resource_parquet.get("markdown_snippet")
        assert "renku" in resource_parquet.get("markdown_snippet")
        assert "SQL" in resource_parquet.get("markdown_snippet")
        assert resource_parquet.get("package_id") in resource_parquet.get(
            "markdown_snippet"
        )

        resource_geojson = factories.Resource(
            format="geoJSON", description="My super geoJSON"
        )
        assert resource_geojson.get("markdown_snippet")
        assert "renku" in resource_geojson.get("markdown_snippet")
        assert "SQL" not in resource_geojson.get("markdown_snippet")
        assert resource_geojson.get("package_id") in resource_geojson.get(
            "markdown_snippet"
        )

        resource_xml = factories.Resource(title="My super XML", format="XML")
        assert not resource_xml.get("markdown_snippet")

        resource_no_format = factories.Resource(title="No format", format="")
        assert not resource_no_format.get("markdown_snippet")

    def test_markdown_snippet_value_on_resource_updates(self):

        resource_vanilla = factories.Resource(title="No format", id="vanilla-resource")

        resource_vanilla = helpers.call_action(
            "resource_patch",
            id=resource_vanilla.get("id"),
            description="TXT Resource with markdown_snippet text",
            format="TXT",
        )
        assert not resource_vanilla.get("markdown_snippet")

        resource_vanilla = helpers.call_action(
            "resource_patch",
            id=resource_vanilla.get("id"),
            description="TXT Resource with markdown_snippet text",
            markdown_snippet="This placeholder should not be overwritten.",
            format="TXT",
        )
        assert resource_vanilla.get("markdown_snippet")
        assert "This placeholder should not be overwritten." in resource_vanilla.get(
            "markdown_snippet"
        )

        resource_vanilla = helpers.call_action(
            "resource_patch",
            id=resource_vanilla.get("id"),
            description="CSV Resource with markdown_snippet text",
            format="CSV",
        )
        assert "This placeholder should not be overwritten." in resource_vanilla.get(
            "markdown_snippet"
        )

        resource_vanilla = helpers.call_action(
            "resource_patch",
            id=resource_vanilla.get("id"),
            description="CSV Resource without markdown_snippet text",
            markdown_snippet="",
        )
        assert resource_vanilla.get("markdown_snippet")
        assert "renku" in resource_vanilla.get("markdown_snippet")
        assert "SQL" in resource_vanilla.get("markdown_snippet")
