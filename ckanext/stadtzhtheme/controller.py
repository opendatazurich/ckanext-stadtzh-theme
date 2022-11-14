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
            c.package = get_action('package_show')(
                context, {'id': package_name})
        except (NotFound, NotAuthorized):
            abort(404, _('Dataset not found'))

        for resource in c.package.get('resources', []):
            if resource['name'] == resource_name:
                c.resource = resource
                break
        if not c.resource:
            abort(404, _('Resource not found'))

        if resource.get('url_type') == 'upload':
            return self._get_download_details(resource)
        elif 'url' not in resource:
            abort(404, _('No download is available'))
        h.redirect_to(resource['url'])

    def _get_download_details(self, resource):
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
