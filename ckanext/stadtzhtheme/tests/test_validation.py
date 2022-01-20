import nose
from ckanapi import TestAppCKAN, ValidationError
from ckan.tests import helpers, factories

eq_ = nose.tools.eq_
assert_true = nose.tools.assert_true


class TestValidation(helpers.FunctionalTestBase):

    def test_invalid_url(self):
        """Test that an invalid resource url is caught by our validator.
        """
        factories.Sysadmin(apikey="my-test-key")
        app = self._get_test_app()
        demo = TestAppCKAN(app, apikey="my-test-key")

        try:
            dataset = factories.Dataset()
            demo.action.resource_create(
                package_id=dataset['name'],
                name='Test-File',
                url='https://example.com]'
            )
        except ValidationError as e:
            eq_(
                e.error_dict['url'],
                [u'Bitte eine valide URL angeben']
            )
        else:
            raise AssertionError('ValidationError not raised')

    def test_invalid_url_for_upload_resource_type(self):
        """Test that the resource url is not validated if the url_type
        is 'upload'.
        """
        factories.Sysadmin(apikey="my-test-key")
        app = self._get_test_app()
        demo = TestAppCKAN(app, apikey="my-test-key")

        try:
            dataset = factories.Dataset()
            demo.action.resource_create(
                package_id=dataset['name'],
                name='Test-File',
                url='https://example.com]',
                url_type='upload'
            )
        except ValidationError as e:
            raise AssertionError('ValidationError raised erroneously')
