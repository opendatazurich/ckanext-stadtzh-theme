# -*- coding: utf-8 -*-

import logging
import json
import re

import ckan.plugins as plugins
import ckan.plugins.toolkit as tk

def create_updateInterval():
    '''Create update interval vocab and tags, if they don't exist already.'''
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    context = {'user': user['name']}
    try:
        data = {'id': 'updateInterval'}
        tk.get_action('vocabulary_show')(context, data)
        logging.info("Update interval vocabulary already exists, skipping.")
    except tk.ObjectNotFound:
        logging.info("Creating vocab 'updateInterval'")
        data = {'name': 'updateInterval'}
        vocab = tk.get_action('vocabulary_create')(context, data)
        for tag in (
            u'   ',
            u'laufend',
            u'jaehrlich',
            u'halbjaehrlich',
            u'quartalsweise',
            u'monatlich',
            u'woechentlich',
            u'taeglich',
            u'sporadisch oder unregelmaessig',
            u'keines'
        ):
            logging.info(
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
        logging.info("Data type vocabulary already exists, skipping.")
    except tk.ObjectNotFound:
        logging.info("Creating vocab 'dataType'")
        data = {'name': 'dataType'}
        vocab = tk.get_action('vocabulary_create')(context, data)
        for tag in (
            u'   ',
            u'Einzeldaten',
            u'Datenaggregat',
            u'Web-Service'
        ):
            logging.info(
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
    return tk.get_action('group_list')(context, data_dict)


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
        extras = package_dict['extras']
        results = {
            'dataType': '   ',
            'updateInterval': '   '
        }
        for extra in extras:
            if extra['key'] == u'dataType':
                results['dataType'] = extra['value']
            if extra['key'] == u'updateInterval':
                results['updateInterval'] = extra['value']
        return results
    except KeyError:
        return results


def get_package_dict(datasetID):
    user = tk.get_action('get_site_user')({}, {})
    context = {'user': user['name']}
    return tk.get_action('package_show')(context, {'id': datasetID})


def validate_date(datestring):
    m = re.match('^[0-9]{2}\.[0-9]{2}\.[0-9]{4}(, [0-9]{2}:[0-9]{2})?$', datestring)
    if m:
        return datestring
    else:
        return False


class IFacetPlugin(plugins.SingletonPlugin):

    plugins.implements(plugins.IFacets, inherit=True)

    def dataset_facets(self, facets_dict, dataset_type):

        facets_dict = {'extras_updateInterval': 'Update Interval', 'tags': 'Keywords', 'organization': 'Organizations', 'res_format': ('File Format')}

        return facets_dict


class StadtzhThemePlugin(plugins.SingletonPlugin,
                         tk.DefaultDatasetForm):

    plugins.implements(plugins.IConfigurer, inherit=False)
    plugins.implements(plugins.IDatasetForm, inherit=False)
    plugins.implements(plugins.ITemplateHelpers, inherit=False)

    # These record how many times methods that this plugin's methods are
    # called, for testing purposes.
    num_times_new_template_called = 0
    num_times_read_template_called = 0
    num_times_edit_template_called = 0
    num_times_comments_template_called = 0
    num_times_search_template_called = 0
    num_times_history_template_called = 0
    num_times_package_form_called = 0
    num_times_check_data_dict_called = 0
    num_times_setup_template_variables_called = 0

    def update_config(self, config):

        tk.add_template_directory(config, 'templates')
        tk.add_public_directory(config, 'public')
        tk.add_resource('fanstatic', 'stadtzhtheme')

        config['ckan.site_logo'] = '/logo.png'

    def get_helpers(self):
        return {
            'updateInterval': updateInterval,
            'dataType': dataType,
            'load_json': load_json,
            'groups': groups,
            'package_has_group': package_has_group,
            'get_tag_vocab_values': get_tag_vocab_values,
            'get_package_dict': get_package_dict,
            'validate_date': validate_date
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
            'comments': [tk.get_validator('ignore_missing'),
                         tk.get_converter('convert_to_extras')]
        })

        # Add update interval as extra field
        schema.update({
            'dataType': [tk.get_validator('ignore_missing'),
                         tk.get_converter('convert_to_tags')('dataType')]
        })

        # Add attributes as extra field
        schema.update({
            'attributes': [tk.get_validator('ignore_missing'),
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
            'comments': [tk.get_converter('convert_from_extras'),
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
            'attributes': [tk.get_converter('convert_from_extras'),
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

    # These methods just record how many times they're called, for testing
    # purposes.
    # TODO: It might be better to test that custom templates returned by
    # these methods are actually used, not just that the methods get
    # called.

    def setup_template_variables(self, context, data_dict):
        StadtzhThemePlugin.num_times_setup_template_variables_called += 1
        return super(StadtzhThemePlugin, self).setup_template_variables(
            context, data_dict)

    def new_template(self):
        StadtzhThemePlugin.num_times_new_template_called += 1
        return super(StadtzhThemePlugin, self).new_template()

    def read_template(self):
        StadtzhThemePlugin.num_times_read_template_called += 1
        return super(StadtzhThemePlugin, self).read_template()

    def edit_template(self):
        StadtzhThemePlugin.num_times_edit_template_called += 1
        return super(StadtzhThemePlugin, self).edit_template()

    def comments_template(self):
        StadtzhThemePlugin.num_times_comments_template_called += 1
        return super(StadtzhThemePlugin, self).comments_template()

    def search_template(self):
        StadtzhThemePlugin.num_times_search_template_called += 1
        return super(StadtzhThemePlugin, self).search_template()

    def history_template(self):
        StadtzhThemePlugin.num_times_history_template_called += 1
        return super(StadtzhThemePlugin, self).history_template()

    def package_form(self):
        StadtzhThemePlugin.num_times_package_form_called += 1
        return super(StadtzhThemePlugin, self).package_form()

    # check_data_dict() is deprecated, this method is only here to test that
    # legacy support for the deprecated method works.
    def check_data_dict(self, data_dict, schema=None):
        StadtzhThemePlugin.num_times_check_data_dict_called += 1
