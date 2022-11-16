import pytest
from ckanapi import ValidationError
from ckan.tests import helpers, factories
from ckantoolkit import config


@pytest.mark.ckan_config("ckan.plugins", "stadtzhtheme")
@pytest.mark.usefixtures("clean_db", "with_plugins")
class TestValidation(object):

    def test_invalid_url(self):
        """Test that an invalid resource url is caught by our validator.
        """
        print(config.get('ckan.plugins'))
        try:
            dataset = factories.Dataset()
            helpers.call_action(
                'resource_download_permalink',
                {},
                package_id=dataset['name'],
                name='Test-File',
                url='https://example.com]'
            )
        except ValidationError as e:
            assert e.error_dict['url'] == [u'Bitte eine valide URL angeben']
        else:
            raise AssertionError('ValidationError not raised')

    def test_invalid_url_for_upload_resource_type(self):
        """Test that the resource url is not validated if the url_type
        is 'upload'.
        """
        try:
            dataset = factories.Dataset()
            helpers.call_action(
                'resource_create',
                package_id=dataset['name'],
                name='Test-File',
                url='https://example.com]',
                url_type='upload'
            )
        except ValidationError:
            raise AssertionError('ValidationError raised erroneously')
