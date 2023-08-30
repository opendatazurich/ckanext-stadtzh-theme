import logging
import mimetypes
from typing import Optional, Union

import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.lib.uploader as uploader
import ckan.logic as logic
import ckan.model as model
from ckan.common import _, c, current_user, request
from ckan.lib import signals
from ckan.plugins import toolkit as tk
from ckan.types import Context, Response
from flask import Blueprint, make_response, send_file
from werkzeug.wrappers.response import Response as WerkzeugResponse

get_action = logic.get_action
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
abort = tk.abort


ogdzh_dataset = Blueprint("ogdzh_resource", __name__, url_prefix="/dataset")


def resource_download_permalink(
    package_name: str, resource_name: str, filename: Optional[str] = None
) -> Union[Response, WerkzeugResponse]:
    """
    Copied from ckan 2.10 source code but using package name and resource name
    instead of ids. This will allow accessing resources of a package by
    filename, giving a link that will not change even if a resource is deleted
    and reuploaded with a new id.
    """
    context: Context = {"user": current_user.name, "auth_user_obj": current_user}

    try:
        rsc = get_action("resource_show")(context, {"id": resource_name})
        get_action("package_show")(context, {"id": package_name})
    except NotFound:
        return base.abort(404, _("Resource not found"))
    except NotAuthorized:
        return base.abort(403, _("Not authorized to download resource"))

    if rsc.get("url_type") == "upload":
        upload = uploader.get_resource_uploader(rsc)
        filepath = upload.get_path(rsc["id"])
        resp = send_file(filepath)

        if rsc.get("mimetype"):
            resp.headers["Content-Type"] = rsc["mimetype"]
        signals.resource_download.send(resource_name)
        return resp

    elif "url" not in rsc:
        return base.abort(404, _("No download is available"))
    return h.redirect_to(rsc["url"])


ogdzh_dataset.add_url_rule(
    "/<package_name>/download/<resource_name>", view_func=resource_download_permalink
)
