import nose
from ckan.tests import helpers, factories
from ckan.lib.helpers import url_for

import ckanext.stadtzhtheme.plugin as plugin

eq_ = nose.tools.eq_
assert_true = nose.tools.assert_true


class TestPlugin(helpers.FunctionalTestBase):

    def test_descr_file(self):
        theme_plugin = plugin.StadtzhThemePlugin()

        expected_keys = ['zip', 'wms', 'wmts', 'wfs', 'kml', 'kmz', 'json', 'csv', 'gpkg'] 
        descr = theme_plugin.descr_config
        assert all(k in descr.keys() for k in expected_keys), "Keys: %s" % descr.keys()

    def test_resource_description_value(self):
        theme_plugin = plugin.StadtzhThemePlugin()
        res = {'format': 'CSV', 'description': 'My super CSV'} 
        eq_(theme_plugin.get_resource_descriptions(res), ['My super CSV'])

    def test_resource_description_file(self):
        theme_plugin = plugin.StadtzhThemePlugin()
        res = {'format': 'CSV', 'description': ''} 

        descr = theme_plugin.get_resource_descriptions(res)

        eq_(len(descr), 2)
        eq_(descr[0], 'Comma-Separated Values.') 
        eq_(descr[1], 'Weitere Informationen zu CSV finden Sie in unserer Rubrik Werkstatt unter [Informationen zu Datenformaten.](https://www.stadt-zuerich.ch/portal/de/index/ogd/werkstatt/csv.html)') 

    def test_translations_without_orgs(self):
        dataset = factories.Dataset()

        url = url_for('dataset_read', id=dataset['name'])
        app = self._get_test_app()
        response = app.get(url)

        assert 'Aktualisierungs&shy;datum' in response, response
        assert not 'Date last updated' in response, response

    def test_translations_with_org(self):
        org = factories.Organization()
        dataset = factories.Dataset(owner_org=org['id'])

        url = url_for('dataset_read', id=dataset['name'])
        app = self._get_test_app()
        response = app.get(url)

        assert 'Aktualisierungs&shy;datum' in response, response
        assert not 'Date last updated' in response, response

    def test_translation_with_en_locale(self):
        org = factories.Organization()
        dataset = factories.Dataset(owner_org=org['id'])

        url = url_for('dataset_read', id=dataset['name'], locale='en')
        app = self._get_test_app()
        response = app.get(url)

        assert not 'Aktualisierungs&shy;datum' in response, response
        assert 'Date last updated' in response, response
