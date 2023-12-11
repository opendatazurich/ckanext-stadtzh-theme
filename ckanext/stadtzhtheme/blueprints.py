from typing import Optional, Union

import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.lib.uploader as uploader
import ckan.logic as logic
from ckan.common import _, current_user
from ckan.lib import munge, signals
from ckan.plugins import toolkit as tk
from ckan.types import Context, Response
from flask import Blueprint, send_file
from werkzeug.wrappers.response import Response as WerkzeugResponse

get_action = logic.get_action
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
abort = tk.abort

ogdzh_dataset = Blueprint("ogdzh_dataset", __name__, url_prefix="/dataset")


def s3filestore_download(
    package_name: str, filename: str, resource_id: str, context: Context
):
    """
    Method will be used to reformat the url to the s3 based download url which
    allow to download the file from s3 instead of filestore. The fallback is handled
    within the s3filestore extension.
    """
    filename = munge.munge_filename(filename)
    return (
        f"{tk.config.get('ckan.site_url')}/dataset/{package_name}/resource/"
        f"{resource_id}/download/{filename}"
    )


def resource_download_permalink(
    package_name: str, resource_name: str, filename: Optional[str] = None
) -> Union[Response, WerkzeugResponse]:
    """Allow accessing resources of a package by resource name, giving a link that
    will not change even if a resource is deleted and reuploaded with a new id.
    """
    context: Context = {"user": current_user.name, "auth_user_obj": current_user}
    rsc = None

    try:
        package = get_action("package_show")(context, {"id": package_name})
        for res in package["resources"]:
            # If the resource names match, this is the resource we want
            if res["name"] == resource_name:
                # Search for the resource using its id, to make sure it exists
                rsc = get_action("resource_show")(context, {"id": res["id"]})
                break
    except NotFound:
        return base.abort(404, _("Resource not found"))
    except NotAuthorized:
        return base.abort(403, _("Not authorized to download resource"))

    if "s3filestore" in tk.config.get("ckan.plugins"):
        # s3filestore needs the filename of the resource, not its name
        resource_filename = rsc.get("filename", resource_name)
        url = s3filestore_download(
            package_name, resource_filename, rsc.get("id"), context
        )
        return h.redirect_to(url)

    if rsc.get("url_type") == "upload":
        upload = uploader.get_resource_uploader(rsc)
        filepath = upload.get_path(rsc["id"])
        resp = send_file(filepath, download_name=resource_name)

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
