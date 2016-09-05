# -*- coding: utf-8 -*-

import logging
import json
import yaml
import re
import os
import pwd
import grp
import urlparse
import traceback
import lepl.apps.rfc3696

from pylons import config
import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
from ckan import model
from ckan.common import request
from routes import url_for
from ckan.lib.uploader import Upload as DefaultUpload
from ckan.lib.uploader import ResourceUpload as DefaultResourceUpload

log = logging.getLogger(__name__)

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
            u'jaehrlich',
            u'halbjaehrlich',
            u'quartalsweise',
            u'monatlich',
            u'woechentlich',
            u'taeglich',
            u'stuendlich',
            u'Echtzeit',
            u'sporadisch oder unregelmaessig',
            u'keines'
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
        return sorted(groups, key=lambda group: group.get('packages', 0))[-1:-(n+1):-1]
    else:
        return sorted(groups, key=lambda group: group.get('packages', 0))[::-1]


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

def is_url(*args, **kw):
    '''
    Returns True if argument parses as a http, https or ftp URL
    '''
    if not args:
        return False
    try:
        url = urlparse.urlparse(args[0])
    except ValueError:
        return False

    valid_schemes = ('http', 'https', 'ftp')
    return url.scheme in valid_schemes

def get_ajax_api_endpoint():
    '''
    Returns the URL endpoint for AJAX calls.
    Depending on the request, it could be the internal or external site URL
    '''
    try:
        request_url = urlparse.urlparse(request.url)
        internal_url = urlparse.urlparse(config.get('ckan.site_url_internal', 'https://ogd.global.szh.loc'))
        if request_url.netloc == internal_url.netloc:
            return config.get('ckan.site_url_internal')
    except ValueError:
        pass
    return config.get('ckan.site_url')

def full_external_url():
    ''' Returns the fully qualified current external url (eg http://...) useful
    for sharing etc '''
    return url_for(
        request.environ['CKAN_CURRENT_URL'],
        host=get_site_host(),
        protocol=get_site_protocol(),
        qualified=True
    )

def get_site_protocol():
    site_url = config.get('ckan.site_url', 'https://data.stadt-zuerich.ch')
    parsed_url = urlparse.urlparse(site_url)
    return parsed_url.scheme.encode('utf-8')

def get_site_host():
    site_url = config.get('ckan.site_url', 'https://data.stadt-zuerich.ch')
    parsed_url = urlparse.urlparse(site_url)
    return parsed_url.netloc.encode('utf-8')

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
                         tk.DefaultDatasetForm):

    plugins.implements(plugins.IConfigurer, inherit=False)
    plugins.implements(plugins.IDatasetForm, inherit=False)
    plugins.implements(plugins.ITemplateHelpers, inherit=False)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IUploader, inherit=True)

    def update_config(self, config):
        try:
            with open(config.get('ckanext.stadtzh-theme.descr_file'), 'r') as descr_file:
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
            'full_external_url': full_external_url,
            'get_ajax_api_endpoint': get_ajax_api_endpoint,
            'is_url': is_url,
            'get_site_protocol': get_site_protocol,
            'get_site_host': get_site_host,
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

    def after_show(self, context, pkg_dict):
        # set value of new field data_publisher with value of url
        pkg_dict['data_publisher'] = pkg_dict['url']

    def before_index(self, search_data):
        if not self.is_supported_package_type(search_data):
            return search_data

        validated_dict = json.loads(search_data['validated_data_dict'])
        search_data['res_format'] = list(set([r['format'].lower() for r in validated_dict[u'resources'] if 'format' in r]))
        return search_data

    def is_supported_package_type(self, pkg_dict):
        # only package type 'dataset' is supported (not harvesters!)
        return pkg_dict.get('type') == 'dataset'

    # IUploader

    def get_uploader(self, upload_to, old_filename=None):
        return StadtzhUpload(upload_to, old_filename)

    def get_resource_uploader(self, data_dict):
        return StadtzhResourceUpload(data_dict)

class StadtzhFileHelper(object):
    def chown_path(self, path, user=None, group=None):
        # try to get uid and guid
        try:
            if user is None:
                uid = self._get_uid(config.get('ckanext.stadtzh-theme.upload_user', None))
            else:
                uid = self._get_uid(user)
        except (KeyError, TypeError):
            uid = -1  # if user cannot be found, use -1 => chown keeps the current user

        try:
            if group is None:    
                gid = self._get_gid(config.get('ckanext.stadtzh-theme.upload_group', None))
            else:
                gid = self._get_gid(group)
        except (KeyError, TypeError):
            gid = -1  # if group cannot be found, use -1 => chown keeps the current group

        # chown file or directory
        if os.path.isfile(path):
            try:
                os.chown(path, uid, gid)
            except OSError:
                log.exception('Tried to change ownership (%s/%s) of %s' % (uid, gid, path))
        else:
            for root, dirs, files in os.walk(path):
                try:
                    current_path = None
                    for name in dirs: 
                        current_path = os.path.join(root, name)
                        os.chown(current_path, uid, gid)
                    for name in files:
                        current_path = os.path.join(root, name)
                        os.chown(current_path, uid, gid)
                except OSError:
                    log.exception('Tried to change ownership (%s/%s) of %s' % (uid, gid, current_path))

    def _get_uid(self, user):
        try:
            return int(user)
        except (ValueError, TypeError):
            return pwd.getpwnam(user).pw_uid

    def _get_gid(self, group):
        try:
            return int(group)
        except (ValueError, TypeError):
            return grp.getgrnam(group).gr_gid


class StadtzhUpload(DefaultUpload, StadtzhFileHelper):
    # copy from https://github.com/ckan/ckan/blob/ckan-2.5.2/ckan/lib/uploader.py
    # add code to change ownership after upload (self.chown_path)
    def upload(self, max_size=2):
        ''' Actually upload the file.
        This should happen just before a commit but after the data has
        been validated and flushed to the db. This is so we do not store
        anything unless the request is actually good.
        max_size is size in MB maximum of the file'''

        if self.filename:
            output_file = open(self.tmp_filepath, 'wb')
            self.upload_file.seek(0)
            current_size = 0
            while True:
                current_size = current_size + 1
                # MB chunks
                data = self.upload_file.read(2 ** 20)
                if not data:
                    break
                output_file.write(data)
                if current_size > max_size:
                    os.remove(self.tmp_filepath)
                    raise logic.ValidationError(
                        {self.file_field: ['File upload too large']}
                    )
            output_file.close()
            os.rename(self.tmp_filepath, self.filepath)
            self.chown_path(self.filepath)
            self.clear = True

        if (self.clear and self.old_filename
                and not self.old_filename.startswith('http')):
            try:
                os.remove(self.old_filepath)
            except OSError:
                pass


class StadtzhResourceUpload(DefaultResourceUpload, StadtzhFileHelper):
    # copy from https://github.com/ckan/ckan/blob/ckan-2.5.2/ckan/lib/uploader.py
    # add code to change ownership after upload (self.chown_path)
    def upload(self, id, max_size=10):
        '''Actually upload the file.

        :returns: ``'file uploaded'`` if a new file was successfully uploaded
            (whether it overwrote a previously uploaded file or not),
            ``'file deleted'`` if an existing uploaded file was deleted,
            or ``None`` if nothing changed
        :rtype: ``string`` or ``None``

        '''
        if not self.storage_path:
            return

        # Get directory and filepath on the system
        # where the file for this resource will be stored
        directory = self.get_directory(id)
        filepath = self.get_path(id)

        # If a filename has been provided (a file is being uploaded)
        # we write it to the filepath (and overwrite it if it already
        # exists). This way the uploaded file will always be stored
        # in the same location
        if self.filename:
            try:
                os.makedirs(directory)
            except OSError, e:
                # errno 17 is file already exists
                if e.errno != 17:
                    raise
            self.chown_path(self.storage_path)

            tmp_filepath = filepath + '~'
            output_file = open(tmp_filepath, 'wb+')
            self.upload_file.seek(0)
            current_size = 0
            while True:
                current_size = current_size + 1
                # MB chunks
                data = self.upload_file.read(2 ** 20)
                if not data:
                    break
                output_file.write(data)
                if current_size > max_size:
                    os.remove(tmp_filepath)
                    raise logic.ValidationError(
                        {'upload': ['File upload too large']}
                    )
            output_file.close()
            os.rename(tmp_filepath, filepath)
            self.chown_path(filepath)
            return

        # The resource form only sets self.clear (via the input clear_upload)
        # to True when an uploaded file is not replaced by another uploaded
        # file, only if it is replaced by a link to file.
        # If the uploaded file is replaced by a link, we should remove the
        # previously uploaded file to clean up the file system.
        if self.clear:
            try:
                os.remove(filepath)
            except OSError, e:
                pass
