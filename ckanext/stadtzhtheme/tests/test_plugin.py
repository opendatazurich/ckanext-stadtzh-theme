import nose
from ckan.tests import helpers

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

        descr = theme_plugin.get_descr_config()
        eq_(descr.keys(), ['zip', 'wms', 'wmts', 'wfs', 'kml', 'kmz', 'json', 'csv', 'gpkg'])
