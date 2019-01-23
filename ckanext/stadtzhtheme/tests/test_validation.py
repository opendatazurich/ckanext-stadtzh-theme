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
                    'url': 'https://example.com]'
		
		}
            )
        except ValidationError as e:
            eq_(
                e.error_dict['url'],
                    [u'Please provide a valid URL']
            )
        else:
            raise AssertionError('ValidationError not raised')
