import nose
from ckanapi import LocalCKAN, ValidationError
from ckan.tests import helpers, factories

eq_ = nose.tools.eq_
assert_true = nose.tools.assert_true


class TestValidation(helpers.FunctionalTestBase):
    def test_invalid_url(self):
        lc = LocalCKAN()

        try:
            dataset = factories.Dataset()
            lc.call_action(
		'resource_create',
		{
                    'package_id': dataset['name'],
                    'name': 'Test-File',
                    'url': '<![CDATA[https://ogd-test.intra.stzh.ch/geoportal/geodatensatz/250]]>'
		
		}
            )
        except ValidationError as e:
            eq_(
                e.error_dict['url'],
                    ['Value must be one of: bactrian; hybrid; f2hybrid; snowwhite; black (not \'rocker\')']
            )
        else:
            raise AssertionError('ValidationError not raised')
