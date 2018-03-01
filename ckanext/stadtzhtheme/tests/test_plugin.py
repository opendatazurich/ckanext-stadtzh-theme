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
        descr = theme_plugin.get_descr_config()
        assert all(k in descr.keys() for k in expected_keys), "Keys: %s" % descr.keys()

    def test_translations_without_orgs(self):
        dataset = factories.Dataset()

        url = url_for('dataset_read', id=dataset['id'])
        app = self._get_test_app()
        response = app.get(url)

        assert 'Aktualisierungsdatum' in response, response
        assert not 'Date last updated' in response, response

    def test_translations_with_org(self):
        org = factories.Organization()
        dataset = factories.Dataset(owner_org=org['id'])

        url = url_for('dataset_read', id=dataset['id'])
        app = self._get_test_app()
        response = app.get(url)

        assert 'Aktualisierungsdatum' in response, response
        assert not 'Date last updated' in response, response

    @helpers.change_config('ckan.locale_default', 'en')
    def test_translation_with_en_locale(self):
        org = factories.Organization()
        dataset = factories.Dataset(owner_org=org['id'])

        url = url_for('dataset_read', id=dataset['id'])
        app = self._get_test_app()
        response = app.get(url)

        assert not 'Aktualisierungsdatum' in response, response
        assert 'Date last updated' in response, response
