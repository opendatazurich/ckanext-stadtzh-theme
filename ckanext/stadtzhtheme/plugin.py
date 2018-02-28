# -*- coding: utf-8 -*-

import logging
import json
import yaml
import re
import lepl.apps.rfc3696
import os.path
from datetime import datetime

from pylons import config
import ckan.plugins as plugins
import ckanext.datapusher.interfaces as dpi
import ckan.plugins.toolkit as tk
from ckan.lib.plugins import DefaultTranslation
from ckan import model

log = logging.getLogger(__name__)

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def create_updateInterval():
    '''Create update interval vocab and tags, if they don't exist already.'''
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    context = {'user': user['name']}
    try:
        data = {'id': 'updateInterval'}
        tk.get_action('vocabulary_show')(context, data)
        log.info("Update interval vocabulary already exists, skipping.")
    except tk.ObjectNotFound:
        log.info("Creating vocab 'updateInterval'")
        data = {'name': 'updateInterval'}
        vocab = tk.get_action('vocabulary_create')(context, data)
        for tag in (
            u'   ',
            u'laufend',
            u'alle 4 Jahre',
            u'jaehrlich',
            u'halbjaehrlich',
            u'quartalsweise',
            u'monatlich',
            u'vierzehntäglich',
            u'woechentlich',
            u'taeglich',
            u'stuendlich',
            u'Echtzeit',
            u'sporadisch oder unregelmaessig',
            u'keines',
            u'laufende Nachfuehrung',
            u'keine Nachfuehrung',
        ):
            log.info(
                "Adding tag {0} to vocab 'updateInterval'".format(tag))
            data = {'name': tag, 'vocabulary_id': vocab['id']}
            tk.get_action('tag_create')(context, data)


def updateInterval():
    '''Return the list of intervals from the updateInterval vocabulary.'''
    create_updateInterval()
    try:
        updateInterval = tk.get_action('tag_list')(
            data_dict={'vocabulary_id': 'updateInterval'})
        return updateInterval
    except tk.ObjectNotFound:
        return None


def create_dataType():
    '''Create update interval vocab and tags, if they don't exist already.'''
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    context = {'user': user['name']}
    try:
        data = {'id': 'dataType'}
        tk.get_action('vocabulary_show')(context, data)
        log.info("Data type vocabulary already exists, skipping.")
    except tk.ObjectNotFound:
        log.info("Creating vocab 'dataType'")
        data = {'name': 'dataType'}
        vocab = tk.get_action('vocabulary_create')(context, data)
        for tag in (
            u'   ',
            u'Bilddatei',
            u'Einzeldaten',
            u'Datenaggregat',
            u'Web-Service'
        ):
            log.info(
                "Adding tag {0} to vocab 'dataType'".format(tag))
            data = {'name': tag, 'vocabulary_id': vocab['id']}
            tk.get_action('tag_create')(context, data)


def dataType():
    '''Return the list of intervals from the dataType vocabulary.'''
    create_dataType()
    try:
        dataType = tk.get_action('tag_list')(
            data_dict={'vocabulary_id': 'dataType'})
        return dataType
    except tk.ObjectNotFound:
        return None


def groups():
    user = tk.get_action('get_site_user')({}, {})
    context = {'user': user['name']}
    data_dict = {
        'all_fields': True,
    }
    try:
        return tk.get_action('group_list')(context, data_dict)
    except tk.ObjectNotFound:
        return None
    
    
def biggest_groups(n):
    '''
    Returns the n biggest groups, to display on start page.
    '''
    user = tk.get_action('get_site_user')({'ignore_auth': True},{})
    context = {'user': user['name']}
    data_dict = {
        'all_fields': True,
    }
    groups = tk.get_action('group_list')(context, data_dict)
    if len(groups) > n:
        return sorted(groups, key=lambda group: group.get('package_count'))[-1:-(n+1):-1]
    else:
        return sorted(groups, key=lambda group: group.get('package_count'))[::-1]


def package_has_group(group_name, groups):
    for group in groups:
        if group_name == group['name']:
            return True
    return False


def load_json(json_data):
    try:
        for kv_pair in json.loads(json_data):
            if not isinstance(kv_pair, list) and len(kv_pair) != 2:
                return False
        return json.loads(json_data)
    except:
        return False


def get_tag_vocab_values(package_dict):
    try:
        return {
            'dataType': package_dict['dataType'],
            'updateInterval': package_dict['updateInterval']
        }
    except KeyError:
        return {
            'dataType': '   ',
            'updateInterval': '   ',
        }


def get_package_dict(datasetID):
    user = tk.get_action('get_site_user')({}, {})
    context = {'user': user['name']}
    try:
        return tk.get_action('package_show')(context, {'id': datasetID})
    except:
        return {}

def get_organization_dict(org=None):
    if org is None:
        return {}
    try:
        return tk.get_action('organization_show')({}, {'id': org})
    except tk.ObjectNotFound:
        return {}

def validate_date(datestring):
    m = re.match('^[0-9]{2}\.[0-9]{2}\.[0-9]{4}(, [0-9]{2}:[0-9]{2})?$', datestring)
    if m:
        return datestring
    else:
        return False

def validate_email(email):
    email_validator = lepl.apps.rfc3696.Email()
    if email_validator(email):
        return email
    else:
        return ''
        

class IFacetPlugin(plugins.SingletonPlugin):

    plugins.implements(plugins.IFacets, inherit=True)

    def dataset_facets(self, facets_dict, dataset_type):

        facets_dict = {'extras_updateInterval': 'Update Interval', 'tags': 'Keywords', 'organization': 'Organizations', 'res_format': ('File Format')}

        return facets_dict


class StadtzhThemePlugin(plugins.SingletonPlugin,
                         tk.DefaultDatasetForm,
                         DefaultTranslation):

    plugins.implements(plugins.IConfigurer, inherit=False)
    plugins.implements(plugins.IDatasetForm, inherit=False)
    plugins.implements(plugins.ITranslation, inherit=False)
    plugins.implements(plugins.ITemplateHelpers, inherit=False)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(dpi.IDataPusher, inherit=True)

    def update_config(self, config):
        try:
            with open(os.path.join(__location__, 'descr.yaml'), 'r') as descr_file:
                self.descr_config = yaml.load(descr_file)
        except IOError:
            self.descr_config = {}

        tk.add_template_directory(config, 'templates')
        tk.add_public_directory(config, 'public')
        tk.add_resource('fanstatic', 'stadtzhtheme')

        config['ckan.site_logo'] = '/logo.png'

    def get_descr_config(self):
        return self.descr_config

    def get_helpers(self):
        return {
            'updateInterval': updateInterval,
            'dataType': dataType,
            'load_json': load_json,
            'groups': groups,
            'biggest_groups': biggest_groups,
            'package_has_group': package_has_group,
            'get_tag_vocab_values': get_tag_vocab_values,
            'get_package_dict': get_package_dict,
            'validate_date': validate_date,
            'validate_email': validate_email,
            'get_organization_dict': get_organization_dict,
            'get_descr_config': self.get_descr_config,
        }

    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return True

    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

    def _modify_package_schema(self, schema):

        # Add spatial relationship as extra field
        schema.update({
            'spatialRelationship': [tk.get_validator('ignore_missing'),
                                    tk.get_converter('convert_to_extras')]
        })

        # Add date first published as extra field
        schema.update({
            'dateFirstPublished': [tk.get_validator('ignore_missing'),
                                   tk.get_converter('convert_to_extras')]
        })

        # Add time range as extra field
        schema.update({
            'timeRange': [tk.get_validator('ignore_missing'),
                          tk.get_converter('convert_to_extras')]
        })

        # Add update interval as extra field
        schema.update({
            'updateInterval': [tk.get_validator('ignore_missing'),
                               tk.get_converter('convert_to_tags')('updateInterval')]
        })

        # Add version as extra field
        schema.update({
            'version': [tk.get_validator('ignore_missing'),
                        tk.get_converter('convert_to_extras')]
        })

        # Add date last updated as extra field
        schema.update({
            'dateLastUpdated': [tk.get_validator('ignore_missing'),
                                tk.get_converter('convert_to_extras')]
        })

        # Add legal information as extra field
        schema.update({
            'legalInformation': [tk.get_validator('ignore_missing'),
                                 tk.get_converter('convert_to_extras')]
        })

        # Add comments as extra field
        schema.update({
            'sszBemerkungen': [tk.get_validator('ignore_missing'),
                         tk.get_converter('convert_to_extras')]
        })

        # Add update interval as extra field
        schema.update({
            'dataType': [tk.get_validator('ignore_missing'),
                         tk.get_converter('convert_to_tags')('dataType')]
        })

        # Add attributes as extra field
        schema.update({
            'sszFields': [tk.get_validator('ignore_missing'),
                           tk.get_converter('convert_to_extras')]
        })

        # Add data quality as extra field
        schema.update({
            'dataQuality': [tk.get_validator('ignore_missing'),
                            tk.get_converter('convert_to_extras')]
        })

        # Add groups as extra field
        schema.update({
            'group': [tk.get_validator('ignore_missing')]
        })

        return schema

    def create_package_schema(self):
        schema = super(StadtzhThemePlugin, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(StadtzhThemePlugin, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def show_package_schema(self):
        schema = super(StadtzhThemePlugin, self).show_package_schema()

        # Don't show vocab tags xed in with normal 'free' tags
        # (e.g. on dataset pages, or on the search page)
        schema['tags']['__extras'].append(tk.get_converter('free_tags_only'))

        # Add our spatialRelationship field to the dataset schema.
        schema.update({
            'spatialRelationship': [tk.get_converter('convert_from_extras'),
                                    tk.get_validator('ignore_missing')]
        })

        # Add our dateFirstPublished field to the dataset schema.
        schema.update({
            'dateFirstPublished': [tk.get_converter('convert_from_extras'),
                                   tk.get_validator('ignore_missing')]
        })

        # Add our timeRange field to the dataset schema.
        schema.update({
            'timeRange': [tk.get_converter('convert_from_extras'),
                          tk.get_validator('ignore_missing')]
        })

        # Add our updateInterval field to the dataset schema.
        schema.update({
            'updateInterval': [tk.get_converter('convert_from_tags')('updateInterval'),
                               tk.get_validator('ignore_missing')]
        })

        # Add our version field to the dataset schema.
        schema.update({
            'version': [tk.get_converter('convert_from_extras'),
                        tk.get_validator('ignore_missing')]
        })

        # Add our dateLastUpdated field to the dataset schema.
        schema.update({
            'dateLastUpdated': [tk.get_converter('convert_from_extras'),
                                tk.get_validator('ignore_missing')]
        })

        # Add our comments field to the dataset schema.
        schema.update({
            'sszBemerkungen': [tk.get_converter('convert_from_extras'),
                         tk.get_validator('ignore_missing')]
        })

        # Add our dataType field to the dataset schema.
        schema.update({
            'dataType': [tk.get_converter('convert_from_tags')('dataType'),
                         tk.get_validator('ignore_missing')]
        })

        # Add our legalInformation field to the dataset schema.
        schema.update({
            'legalInformation': [tk.get_converter('convert_from_extras'),
                                 tk.get_validator('ignore_missing')]
        })

        # Add our attributes field to the dataset schema.
        schema.update({
            'sszFields': [tk.get_converter('convert_from_extras'),
                           tk.get_validator('ignore_missing')]
        })

        # Add our data quality field to the dataset schema.
        schema.update({
            'dataQuality': [tk.get_converter('convert_from_extras'),
                            tk.get_validator('ignore_missing')]
        })

        # Add our groups field to the dataset schema.
        schema.update({
            'group': [tk.get_validator('ignore_missing')]
        })

        return schema

    def setup_template_variables(self, context, data_dict):
        context['descr_config'] = self.descr_config
        return super(StadtzhThemePlugin, self).setup_template_variables(
            context, data_dict)

    # IPackageController

    def before_search(self, data_dict):
        if not data_dict.get('sort'):
            data_dict['sort'] = 'score desc, date_last_modified desc'
        return data_dict

    def after_show(self, context, pkg_dict):
        # set value of new field data_publisher with value of url
        pkg_dict['data_publisher'] = pkg_dict['url']

    def before_index(self, search_data):
        if not self.is_supported_package_type(search_data):
            return search_data

        validated_dict = json.loads(search_data['validated_data_dict'])
        search_data['res_format'] = list(set([r['format'].lower() for r in validated_dict[u'resources'] if 'format' in r]))

        try:
            attributes = load_json(search_data['sszFields'])
            search_data['attribute_names'] = [k for k, v in attributes]
            search_data['attribute_descriptions'] = [v for k, v in attributes]
            del search_data['sszFields']
        except (ValueError, TypeError, KeyError):
            pass

        try:
            search_data['date_last_modified'] = datetime.strptime(search_data['dateLastUpdated'], '%d.%m.%Y').isoformat() + 'Z'
            search_data['date_first_published'] = datetime.strptime(search_data['dateFirstPublished'], '%d.%m.%Y').isoformat() + 'Z'
        except (KeyError, ValueError):
            pass
        return search_data

    def before_view(self, pkg_dict):
        if not self.is_supported_package_type(pkg_dict):
            return pkg_dict

        # create resource views if necessary
        user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
        context = {
            'model': model,
            'session': model.Session,
            'user': user['name']
        }
        tk.check_access('package_create_default_resource_views', context)

        # get the dataset via API, as the pkg_dict does not contain all fields
        dataset = tk.get_action('package_show')(
            context,
            {'id': pkg_dict['id']}
        )

        # Make sure resource views are created before showing a dataset
        tk.get_action('package_create_default_resource_views')(
            context,
            {'package': dataset}
        )

        return pkg_dict

    def is_supported_package_type(self, pkg_dict):
        # only package type 'dataset' is supported (not harvesters!)
        return pkg_dict.get('type') == 'dataset'

    # IDataPusher

    def after_upload(self, context, resource_dict, dataset_dict):
        # create resource views after a successful upload to the DataStore
        tk.get_action('resource_create_default_resource_views')(
            context,
            {
	        'resource': resource_dict,
                'package': dataset_dict,
            }
        )
