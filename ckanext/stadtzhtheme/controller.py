from urllib import urlencode
import logging
import mimetypes

from ckan.plugins import toolkit as tk
import ckan.model as model
import ckan.logic as logic
import ckan.lib.plugins
from ckan.common import c, config, _, request, response, OrderedDict
import ckan.lib.helpers as h
import ckan.lib.uploader as uploader
import ckan.lib.search as search
import ckan.lib.base as base
import paste.fileapp
from six import string_types


import ckan.controllers.group as group
import ckan.controllers.package as package

lookup_group_controller = ckan.lib.plugins.lookup_group_controller
log = logging.getLogger(__name__)
get_action = logic.get_action
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
abort = tk.abort
render = base.render


class OgdzhGroupSearchController(group.GroupController):
    """
    Backporting [https://github.com/ckan/ckan/pull/4032] from CKAN 2.8:
    Improved search in group read and bulk page.

    TODO: remove this controller overwrite after upgrade to CKAN 2.8
    """

    def _read(self, id, limit, group_type): # noqa
        ''' This is common code used by both read and bulk_process'''
        context = {'model': model, 'session': model.Session,
                   'user': c.user,
                   'schema': self._db_to_form_schema(group_type=group_type),
                   'for_view': True, 'extras_as_string': True}

        q = c.q = request.params.get('q', '')

        # This overwrite forces CKAN to use the 'fq' parameter instead of
        # the 'q' parameter for filtering by groups in the solr search query.
        if c.group_dict.get('is_organization'):
            fq = 'owner_org:"%s"' % c.group_dict.get('id')
        else:
            fq = 'groups:"%s"' % c.group_dict.get('name')

        c.description_formatted = \
            h.render_markdown(c.group_dict.get('description'))

        context['return_query'] = True

        page = h.get_page_number(request.params)

        # most search operations should reset the page counter:
        params_nopage = [(k, v) for k, v in request.params.items()
                         if k != 'page']
        sort_by = request.params.get('sort', None)

        def search_url(params):
            controller = lookup_group_controller(group_type)
            action = 'bulk_process' if c.action == 'bulk_process' else 'read'
            url = h.url_for(controller=controller, action=action, id=id)
            params = [(k, v.encode('utf-8')
                      if isinstance(v, string_types) else str(v))
                      for k, v in params]
            return url + u'?' + urlencode(params)

        def drill_down_url(**by):
            return h.add_url_param(alternative_url=None,
                                   controller='group', action='read',
                                   extras=dict(id=c.group_dict.get('name')),
                                   new_params=by)

        c.drill_down_url = drill_down_url

        def remove_field(key, value=None, replace=None):
            controller = lookup_group_controller(group_type)
            return h.remove_url_param(key, value=value, replace=replace,
                                      controller=controller, action='read',
                                      extras=dict(id=c.group_dict.get('name')))

        c.remove_field = remove_field

        def pager_url(q=None, page=None):
            params = list(params_nopage)
            params.append(('page', page))
            return search_url(params)

        try:
            c.fields = []
            c.fields_grouped = {}
            search_extras = {}
            for (param, value) in request.params.items():
                if param not in ['q', 'page', 'sort'] \
                        and len(value) and not param.startswith('_'):
                    if not param.startswith('ext_'):
                        c.fields.append((param, value))
                        q += ' %s: "%s"' % (param, value)
                        if param not in c.fields_grouped:
                            c.fields_grouped[param] = [value]
                        else:
                            c.fields_grouped[param].append(value)
                    else:
                        search_extras[param] = value

            facets = OrderedDict()

            default_facet_titles = {'organization': _('Organizations'),
                                    'groups': _('Groups'),
                                    'tags': _('Tags'),
                                    'res_format': _('Formats'),
                                    'license_id': _('Licenses')}

            for facet in h.facets():
                if facet in default_facet_titles:
                    facets[facet] = default_facet_titles[facet]
                else:
                    facets[facet] = facet

            # Facet titles
            self._update_facet_titles(facets, group_type)

            c.facet_titles = facets

            data_dict = {
                'q': q,
                'fq': fq,
                'include_private': True,
                'facet.field': facets.keys(),
                'rows': limit,
                'sort': sort_by,
                'start': (page - 1) * limit,
                'extras': search_extras
            }

            context_ = dict((k, v) for (k, v) in context.items()
                            if k != 'schema')
            query = get_action('package_search')(context_, data_dict)

            c.page = h.Page(
                collection=query['results'],
                page=page,
                url=pager_url,
                item_count=query['count'],
                items_per_page=limit
            )

            c.group_dict['package_count'] = query['count']

            c.search_facets = query['search_facets']
            c.search_facets_limits = {}
            for facet in c.search_facets.keys():
                limit = int(request.params.get(
                    '_%s_limit' % facet,
                    config.get('search.facets.default', 10)))
                c.search_facets_limits[facet] = limit
            c.page.items = query['results']

            c.sort_by_selected = sort_by

        except search.SearchError as se:
            log.error('Group search error: %r', se.args)
            c.query_error = True
            c.page = h.Page(collection=[])

        self._setup_template_variables(context, {'id': id},
                                       group_type=group_type)


class OgdzhPackageController(package.PackageController):
    def resource_download_permalink(self, package_name, resource_name):
        """
        Copied from PackageController resource_download method, but using
        package name and resource name instead of ids. This will allow
        accessing resources of a package by filename, giving a link that will
        not change even if a resource is deleted and reuploaded with a new id.
        """
        context = {'model': model, 'session': model.Session,
                   'user': c.user,
                   'auth_user_obj': c.userobj,
                   'for_view': True}

        try:
            c.package = get_action('package_show')(context, {'id': package_name})
        except (NotFound, NotAuthorized):
            abort(404, _('Dataset not found'))

        for resource in c.package.get('resources', []):
            if resource['name'] == resource_name:
                c.resource = resource
                break
        if not c.resource:
            abort(404, _('Resource not found'))

        if resource.get('url_type') == 'upload':
            upload = uploader.get_resource_uploader(resource)
            filepath = upload.get_path(resource['id'])
            fileapp = paste.fileapp.FileApp(filepath)
            try:
                status, headers, app_iter = request.call_application(fileapp)
            except OSError:
                abort(404, _('Resource data not found'))
            response.headers.update(dict(headers))
            content_type, content_enc = mimetypes.guess_type(
                resource.get('url', ''))
            if content_type:
                response.headers['Content-Type'] = content_type
            response.status = status
            return app_iter
        elif 'url' not in resource:
            abort(404, _('No download is available'))
        h.redirect_to(resource['url'])
