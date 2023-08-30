import logging
import mimetypes
from flask import Blueprint, make_response, send_file

from ckan.plugins import toolkit as tk
import ckan.model as model
import ckan.logic as logic
from ckan.common import c, _, request
import ckan.lib.helpers as h
import ckan.lib.uploader as uploader

log = logging.getLogger(__name__)
get_action = logic.get_action
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
abort = tk.abort


ogdzh_dataset = Blueprint('ogdzh_resource', __name__, url_prefix='/dataset')


def resource_download_permalink(package_name, resource_name):
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


def _get_download_details(resource):
    upload = uploader.get_resource_uploader(resource)
    filepath = upload.get_path(resource['id'])
    resp = send_file(filepath, download_name=filename)

    response = make_response(resp)
    response.headers.update(dict(headers))
    content_type, content_enc = mimetypes.guess_type(
        resource.get('url', ''))
    if content_type:
        response.headers['Content-Type'] = content_type
    response.status = status
    return app_iter


ogdzh_dataset.add_url_rule('/dataset/{package_name}/download/{resource_name}', view_func=resource_download_permalink)
