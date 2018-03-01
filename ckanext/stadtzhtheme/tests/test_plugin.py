import nose
from ckan.tests import helpers, factories
from ckan.lib.helpers import url_for

import ckanext.stadtzhtheme.plugin as plugin

eq_ = nose.tools.eq_
assert_true = nose.tools.assert_true


class TestPlugin(helpers.FunctionalTestBase):
    def setUp(self):
        return

    def tearDown(self):
        return

    def test_descr_file(self):
        theme_plugin = plugin.StadtzhThemePlugin()

        expected_keys = ['zip', 'wms', 'wmts', 'wfs', 'kml', 'kmz', 'json', 'csv', 'gpkg'] 
        descr = theme_plugin.get_descr_config()
        assert all(k in descr.keys() for k in expected_keys), "Keys: %s" % descr.keys()

    def test_translations(self):
        dataset = factories.Dataset(
            notes='Test dataset'
        )

        url = url_for('dataset_read', id=dataset['id'])
        app = self._get_test_app()
        response = app.get(url)

        assert 'Aktualisierungsdatum' in response, response
