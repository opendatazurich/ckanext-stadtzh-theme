# -*- coding: utf-8 -*-

import json
import logging
import os.path
import re
from datetime import datetime

import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
import yaml
from ckan.lib.plugins import DefaultTranslation
from ckan.logic.validators import url_validator
from validate_email import validate_email

import ckanext.xloader.interfaces as xi
from ckanext.stadtzhtheme import logic as ogdzh_logic
from ckanext.stadtzhtheme.blueprints import ogdzh_dataset
from ckanext.stadtzhtheme.commands import get_commands

log = logging.getLogger(__name__)

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def create_updateInterval():
    """Create update interval vocab and tags, if they don't exist already."""
    user = tk.get_action("get_site_user")({"ignore_auth": True}, {})
    context = {"user": user["name"]}
    try:
        data = {"id": "updateInterval"}
        tk.get_action("vocabulary_show")(context, data)
        log.info("Update interval vocabulary already exists, skipping.")
    except (tk.ObjectNotFound, TypeError):
        # when a NotFound error is raised, a translated error message is
        # generated but it's possible no translator is defined, which leads
        # to a TypeError ("No object (name: translator) has been registered
        # for this thread"). This is the reason we catch TypeError here as well
        log.info("Creating vocab 'updateInterval'")
        data = {"name": "updateInterval"}
        vocab = tk.get_action("vocabulary_create")(context, data)
        for tag in (
            "   ",
            "laufend",
            "alle 4 Jahre",
            "jaehrlich",
            "halbjaehrlich",
            "quartalsweise",
            "monatlich",
            "vierzehntaeglich",
            "woechentlich",
            "taeglich",
            "stuendlich",
            "Echtzeit",
            "sporadisch oder unregelmaessig",
            "keines",
            "laufende Nachfuehrung",
            "keine Nachfuehrung",
        ):
            log.info("Adding tag %s to vocab 'updateInterval'" % tag)
            data = {"name": tag, "vocabulary_id": vocab["id"]}
            tk.get_action("tag_create")(context, data)


def updateInterval():
    """Return the list of intervals from the updateInterval vocabulary."""
    try:
        updateInterval = tk.get_action("tag_list")(
            data_dict={"vocabulary_id": "updateInterval"}
        )
        return updateInterval
    except tk.ObjectNotFound:
        return None


def create_dataType():
    """Create update interval vocab and tags, if they don't exist already."""
    user = tk.get_action("get_site_user")({"ignore_auth": True}, {})
    context = {"user": user["name"]}
    try:
        data = {"id": "dataType"}
        tk.get_action("vocabulary_show")(context, data)
        log.info("Data type vocabulary already exists, skipping.")
    except (tk.ObjectNotFound, TypeError):
        # when a NotFound error is raised, a translated error message is
        # generated but it's possible no translator is defined, which leads
        # to a TypeError ("No object (name: translator) has been registered
        # for this thread"). This is the reason we catch TypeError here as well
        log.info("Creating vocab 'dataType'")
        data = {"name": "dataType"}
        vocab = tk.get_action("vocabulary_create")(context, data)
        for tag in ("   ", "Bilddatei", "Einzeldaten", "Datenaggregat", "Web-Service"):
            log.info("Adding tag %s to vocab 'dataType'" % tag)
            data = {"name": tag, "vocabulary_id": vocab["id"]}
            tk.get_action("tag_create")(context, data)


def dataType():
    """Return the list of intervals from the dataType vocabulary."""
    try:
        dataType = tk.get_action("tag_list")(data_dict={"vocabulary_id": "dataType"})
        return dataType
    except tk.ObjectNotFound:
        return None


def groups():
    user = tk.get_action("get_site_user")({}, {})
    context = {"user": user["name"]}
    data_dict = {
        "all_fields": True,
    }
    try:
        return tk.get_action("group_list")(context, data_dict)
    except tk.ObjectNotFound:
        return None


def biggest_groups(n):
    """
    Returns the n biggest groups, to display on start page.
    """
    user = tk.get_action("get_site_user")({"ignore_auth": True}, {})
    context = {"user": user["name"]}
    data_dict = {
        "all_fields": True,
    }
    groups = tk.get_action("group_list")(context, data_dict)
    if len(groups) > n:
        return sorted(groups, key=lambda group: group.get("package_count"))[
            -1 : -(n + 1) : -1
        ]
    else:
        return sorted(groups, key=lambda group: group.get("package_count"))[::-1]


def package_has_group(group_name, groups):
    for group in groups:
        if group_name == group["name"]:
            return True
    return False


def load_json(json_data):
    try:
        for kv_pair in json.loads(json_data):
            if not isinstance(kv_pair, list) and len(kv_pair) != 2:
                return False
        return json.loads(json_data)
    except Exception:
        return False


def get_package_dict(datasetID):
    user = tk.get_action("get_site_user")({}, {})
    context = {"user": user["name"]}
    try:
        return tk.get_action("package_show")(context, {"id": datasetID})
    except Exception:
        return {}


def get_organization_dict(org=None):
    if org is None:
        return {}
    try:
        return tk.get_action("organization_show")({}, {"id": org})
    except tk.ObjectNotFound:
        return {}


def validate_date(datestring):
    m = re.match(r"^[0-9]{2}\.[0-9]{2}\.[0-9]{4}(, [0-9]{2}:[0-9]{2})?$", datestring)
    if m:
        return datestring
    else:
        return False


def ogdzh_validate_email(email):
    if validate_email(email):
        return email
    else:
        return ""


def validate_url(key, data, errors, context):
    """Skip validating url if the url_type is 'upload'. Otherwise, call CKAN's
    url validator.
    """
    try:
        # generate url_type key from given key
        # key is a tuple like this: ('resources', 0, 'url')
        url_type_key = (key[0], key[1], "url_type")
        url_type = data.get(url_type_key, None)
        if url_type == "upload":
            log.debug("url_type is upload, skipping")
            return
    except IndexError:
        pass

    return url_validator(key, data, errors, context)


def ogdzh_package_create_default_resource_views(context, pkg_dict):
    if not StadtzhThemePlugin.is_supported_package_type(StadtzhThemePlugin, pkg_dict):
        return pkg_dict

    # create resource views if necessary
    tk.check_access("package_create_default_resource_views", context)

    # get the dataset via API, as the pkg_dict does not contain all fields
    dataset = tk.get_action("package_show")(context, {"id": pkg_dict["id"]})

    # Make sure resource views are created before showing a dataset
    tk.get_action("package_create_default_resource_views")(
        context, {"package": dataset}
    )
    StadtzhThemePlugin._replace_resource_download_urls(
        StadtzhThemePlugin, pkg_dict["resources"], pkg_dict["name"]
    )

    return pkg_dict


class IFacetPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IFacets, inherit=True)

    def dataset_facets(self, facets_dict, dataset_type):
        facets_dict = {
            "extras_updateInterval": "Update Interval",
            "tags": "Keywords",
            "organization": "Organizations",
            "res_format": ("File Format"),
        }

        return facets_dict


class StadtzhThemePlugin(
    plugins.SingletonPlugin, tk.DefaultDatasetForm, DefaultTranslation
):
    plugins.implements(plugins.IClick)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IConfigurer, inherit=False)
    plugins.implements(plugins.IDatasetForm, inherit=False)
    plugins.implements(plugins.ITranslation, inherit=False)
    plugins.implements(plugins.ITemplateHelpers, inherit=False)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IBlueprint, inherit=True)
    plugins.implements(plugins.IValidators, inherit=True)
    plugins.implements(plugins.IActions, inherit=True)
    plugins.implements(xi.IXloader, inherit=True)
    plugins.implements(plugins.IResourceController, inherit=True)

    def configure(self, config):
        # create vocabularies if necessary
        create_updateInterval()
        create_dataType()

    def update_config(self, config):
        try:
            with open(os.path.join(__location__, "descr.yaml"), "r") as descr_file:
                self.descr_config = yaml.safe_load(descr_file)
        except IOError:
            self.descr_config = {}

        tk.add_template_directory(config, "templates")
        tk.add_public_directory(config, "public")
        tk.add_resource("assets", "stadtzh_theme")

        config["ckan.site_logo"] = "/logo.png"

    def get_resource_descriptions(self, res):
        res_descr = res.get("description")
        if res_descr:
            return [res_descr]

        file_format = (res.get("format") or "data").lower()
        if self.descr_config.get(file_format):
            link = self.descr_config[file_format]["link"]
            if not link:
                link = ""
            return [
                self.descr_config[file_format]["description"],
                link,
            ]
        return []

    # ITemplateHelpers

    def get_helpers(self):
        return {
            "updateInterval": updateInterval,
            "dataType": dataType,
            "load_json": load_json,
            "groups": groups,
            "biggest_groups": biggest_groups,
            "package_has_group": package_has_group,
            "get_package_dict": get_package_dict,
            "validate_date": validate_date,
            "validate_email": ogdzh_validate_email,
            "get_organization_dict": get_organization_dict,
            "get_resource_descriptions": self.get_resource_descriptions,
        }

    # IActions
    def get_actions(self):
        return {
            "ogdzh_autosuggest": ogdzh_logic.ogdzh_autosuggest,
        }

    # IValidators
    def get_validators(self):
        return {
            "validate_url": validate_url,
        }

    # IDatasetForm
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
        schema.update(
            {
                "spatialRelationship": [
                    tk.get_validator("ignore_missing"),
                    tk.get_converter("convert_to_extras"),
                ]
            }
        )

        # Add date first published as extra field
        schema.update(
            {
                "dateFirstPublished": [
                    tk.get_validator("ignore_missing"),
                    tk.get_converter("convert_to_extras"),
                ]
            }
        )

        # Add time range as extra field
        schema.update(
            {
                "timeRange": [
                    tk.get_validator("ignore_missing"),
                    tk.get_converter("convert_to_extras"),
                ]
            }
        )

        # Add update interval as extra field
        schema.update(
            {
                "updateInterval": [
                    tk.get_validator("ignore_missing"),
                    tk.get_converter("convert_to_tags")("updateInterval"),
                ]
            }
        )

        # Add version as extra field
        schema.update(
            {
                "version": [
                    tk.get_validator("ignore_missing"),
                    tk.get_converter("convert_to_extras"),
                ]
            }
        )

        # Add date last updated as extra field
        schema.update(
            {
                "dateLastUpdated": [
                    tk.get_validator("ignore_missing"),
                    tk.get_converter("convert_to_extras"),
                ]
            }
        )

        # Add legal information as extra field
        schema.update(
            {
                "legalInformation": [
                    tk.get_validator("ignore_missing"),
                    tk.get_converter("convert_to_extras"),
                ]
            }
        )

        # Add comments as extra field
        schema.update(
            {
                "sszBemerkungen": [
                    tk.get_validator("ignore_missing"),
                    tk.get_converter("convert_to_extras"),
                ]
            }
        )

        # Add update interval as extra field
        schema.update(
            {
                "dataType": [
                    tk.get_validator("ignore_missing"),
                    tk.get_converter("convert_to_tags")("dataType"),
                ]
            }
        )

        # Add attributes as extra field
        schema.update(
            {
                "sszFields": [
                    tk.get_validator("ignore_missing"),
                    tk.get_converter("convert_to_extras"),
                ]
            }
        )

        # Add data quality as extra field
        schema.update(
            {
                "dataQuality": [
                    tk.get_validator("ignore_missing"),
                    tk.get_converter("convert_to_extras"),
                ]
            }
        )

        # Add groups as extra field
        schema.update({"group": [tk.get_validator("ignore_missing")]})

        # Add a custom hash field, used to check if a package's resources have
        # been updated. The `hash` field on the resource is updated by xloader
        # but only for files, not for urls, so we need one we can use for both
        schema["resources"].update({"zh_hash": [tk.get_validator("ignore_missing")]})

        # Validate URL with custom validate_url method
        schema["resources"].update(
            {
                "url": [
                    tk.get_validator("ignore_missing"),
                    tk.get_validator("unicode_safe"),
                    tk.get_validator("remove_whitespace"),
                    tk.get_validator("validate_url"),
                ]
            }
        )

        # Add resource field 'filename'
        schema["resources"].update(
            {
                "filename": [
                    tk.get_validator("ignore_missing"),
                    tk.get_validator("unicode_safe"),
                    tk.get_validator("remove_whitespace"),
                ],
            }
        )

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
        schema["tags"]["__extras"].append(tk.get_converter("free_tags_only"))

        # Add our spatialRelationship field to the dataset schema.
        schema.update(
            {
                "spatialRelationship": [
                    tk.get_converter("convert_from_extras"),
                    tk.get_validator("ignore_missing"),
                ]
            }
        )

        # Add our dateFirstPublished field to the dataset schema.
        schema.update(
            {
                "dateFirstPublished": [
                    tk.get_converter("convert_from_extras"),
                    tk.get_validator("ignore_missing"),
                ]
            }
        )

        # Add our timeRange field to the dataset schema.
        schema.update(
            {
                "timeRange": [
                    tk.get_converter("convert_from_extras"),
                    tk.get_validator("ignore_missing"),
                ]
            }
        )

        # Add our updateInterval field to the dataset schema.
        schema.update(
            {
                "updateInterval": [
                    tk.get_converter("convert_from_tags")("updateInterval"),
                    tk.get_validator("ignore_missing"),
                ]
            }
        )

        # Add our version field to the dataset schema.
        schema.update(
            {
                "version": [
                    tk.get_converter("convert_from_extras"),
                    tk.get_validator("ignore_missing"),
                ]
            }
        )

        # Add our dateLastUpdated field to the dataset schema.
        schema.update(
            {
                "dateLastUpdated": [
                    tk.get_converter("convert_from_extras"),
                    tk.get_validator("ignore_missing"),
                ]
            }
        )

        # Add our comments field to the dataset schema.
        schema.update(
            {
                "sszBemerkungen": [
                    tk.get_converter("convert_from_extras"),
                    tk.get_validator("ignore_missing"),
                ]
            }
        )

        # Add our dataType field to the dataset schema.
        schema.update(
            {
                "dataType": [
                    tk.get_converter("convert_from_tags")("dataType"),
                    tk.get_validator("ignore_missing"),
                ]
            }
        )

        # Add our legalInformation field to the dataset schema.
        schema.update(
            {
                "legalInformation": [
                    tk.get_converter("convert_from_extras"),
                    tk.get_validator("ignore_missing"),
                ]
            }
        )

        # Add our attributes field to the dataset schema.
        schema.update(
            {
                "sszFields": [
                    tk.get_converter("convert_from_extras"),
                    tk.get_validator("ignore_missing"),
                ]
            }
        )

        # Add our data quality field to the dataset schema.
        schema.update(
            {
                "dataQuality": [
                    tk.get_converter("convert_from_extras"),
                    tk.get_validator("ignore_missing"),
                ]
            }
        )

        # Add our groups field to the dataset schema.
        schema.update({"group": [tk.get_validator("ignore_missing")]})

        # add a custom hash field
        schema["resources"].update({"zh_hash": [tk.get_validator("ignore_missing")]})

        # Add resource field 'filename'
        schema["resources"].update(
            {
                "filename": [
                    tk.get_validator("ignore_missing"),
                    tk.get_validator("unicode_safe"),
                    tk.get_validator("remove_whitespace"),
                ],
            },
        )

        return schema

    def setup_template_variables(self, context, data_dict):
        context["descr_config"] = self.descr_config
        return super(StadtzhThemePlugin, self).setup_template_variables(
            context, data_dict
        )

    # IPackageController

    def before_dataset_search(self, search_params):
        if not search_params.get("sort"):
            search_params["sort"] = "score desc, date_last_modified desc"
        # Search in our `text_de` field that has been analysed as German text.
        # The CKAN default query fields are the same except they include
        # the `text` field instead.
        search_params["qf"] = "name^4 title^4 tags^2 groups^2 text_de"
        return search_params

    def after_dataset_show(self, context, pkg_dict):
        # set value of new field data_publisher with value of url
        pkg_dict["data_publisher"] = pkg_dict["url"]
        self._replace_resource_download_urls(pkg_dict["resources"], pkg_dict["name"])
        return pkg_dict

    def before_dataset_index(self, search_data):
        if not self.is_supported_package_type(search_data):
            return search_data

        validated_dict = json.loads(search_data["validated_data_dict"])
        search_data["res_format"] = list(
            set(
                [
                    r["format"].lower()
                    for r in validated_dict["resources"]
                    if "format" in r
                ]
            )
        )

        try:
            attributes = load_json(search_data["sszFields"])
            search_data["attribute_names"] = [k for k, v in attributes]
            search_data["attribute_descriptions"] = [v for k, v in attributes]
            del search_data["sszFields"]
        except (ValueError, TypeError, KeyError):
            pass

        try:
            search_data["date_last_modified"] = (
                datetime.strptime(
                    search_data["dateLastUpdated"], "%d.%m.%Y"
                ).isoformat()
                + "Z"
            )
            search_data["date_first_published"] = (
                datetime.strptime(
                    search_data["dateFirstPublished"], "%d.%m.%Y"
                ).isoformat()
                + "Z"
            )
        except (KeyError, ValueError):
            pass

        # clean terms for suggest context
        search_data = self._prepare_suggest_context(search_data, validated_dict)

        return search_data

    def after_dataset_update(self, context, pkg_dict):
        return ogdzh_package_create_default_resource_views(context, pkg_dict)

    def after_dataset_search(self, search_results, search_params):
        for package in search_results["results"]:
            self._replace_resource_download_urls(package["resources"], package["name"])
        return search_results

    def is_supported_package_type(self, pkg_dict):
        # only package type 'dataset' is supported (not harvesters!)
        return pkg_dict.get("type") == "dataset"

    def _replace_resource_download_urls(self, resources, package_name):
        for resource in resources:
            if resource["url_type"] == "upload":
                resource["url"] = "%s/dataset/%s/download/%s" % (
                    tk.config.get("ckanext.stadtzhtheme.frontend_url", ""),
                    package_name,
                    resource["name"],
                )

    def _prepare_suggest_context(self, search_data, pkg_dict):
        def clean_suggestion(term):
            if term:
                term = term.replace("-", "")
            return term

        search_data["cleaned_groups"] = [
            clean_suggestion(t) for t in search_data["groups"]
        ]
        search_data["cleaned_tags"] = [clean_suggestion(t) for t in search_data["tags"]]
        search_data["cleaned_license_id"] = clean_suggestion(search_data["license_id"])
        search_data["cleaned_res_format"] = [
            clean_suggestion(t) for t in search_data["res_format"]
        ]
        return search_data

    # IBlueprint
    def get_blueprint(self):
        return ogdzh_dataset

    # IXloader

    def after_upload(self, context, resource_dict, dataset_dict):
        # create resource views after a successful upload to the DataStore
        tk.get_action("resource_create_default_resource_views")(
            context,
            {
                "resource": resource_dict,
                "package": dataset_dict,
            },
        )

    # IResourceController

    def _set_resource_filename(self, resource):
        if resource.get("url_type") == "upload" and resource.get("upload"):
            upload = resource["upload"]
            if upload.filename:
                resource["filename"] = os.path.basename(upload.filename)

    def before_resource_create(self, context, resource):
        self._set_resource_filename(resource)

        dataset = tk.get_action("package_show")(context, {"id": resource["package_id"]})
        existing_names = [r["name"] for r in dataset["resources"]]
        if resource["name"] in existing_names:
            msg = 'The resource name "{0}" is already in use'.format(resource["name"])
            raise tk.ValidationError({"resources": msg})

    def before_resource_update(self, context, current, resource):
        self._set_resource_filename(resource)

    # IClick

    def get_commands(self):
        return get_commands()
