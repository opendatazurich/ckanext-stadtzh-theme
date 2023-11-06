import itertools
import os
import sys
import traceback

import ckan.logic as logic
import ckan.model as model
from ckan.lib.uploader import get_storage_path
import click


def get_commands():
    return [ogdzh]


@click.group()
def ogdzh():
    pass


@ogdzh.command("cleanup_datastore")
def cleanup_datastore():
    user = logic.get_action("get_site_user")({"ignore_auth": True}, {})
    context = {"model": model, "session": model.Session, "user": user["name"]}
    try:
        logic.check_access("datastore_delete", context)
        logic.check_access("resource_show", context)
    except logic.NotAuthorized:
        print("User is not authorized to perform this action.")
        sys.exit(1)

    # query datastore to get all resources from the _table_metadata
    resource_id_list = []
    try:
        for offset in itertools.count(start=0, step=100):
            print("Load metadata records from datastore (offset: %s)" % offset)
            record_list, has_next_page = _get_datastore_table_page(
                context, offset
            )
            resource_id_list.extend(record_list)
            if not has_next_page:
                break
    except Exception as e:
        print(
            "Error while gathering resources: %s / %s"
            % (str(e), traceback.format_exc())
        )

    # delete the rows of the orphaned datastore tables
    delete_count = 0
    for resource_id in resource_id_list:
        try:
            logic.check_access("datastore_delete", context)
            logic.get_action("datastore_delete")(
                context, {"resource_id": resource_id, "force": True}
            )
            print("Table '%s' deleted (not dropped)" % resource_id)
            delete_count += 1
        except Exception as e:
            print(
                "Error while deleting datastore resource %s: %s / %s"
                % (resource_id, str(e), traceback.format_exc())
            )
            continue

    print("Deleted content of %s tables" % delete_count)


@ogdzh.command("cleanup_filestore")
def cleanup_filestore(self):
    resource_path = _get_resource_storage_path()

    print("\nClean up file storage at {}:\n".format(resource_path))

    user = logic.get_action("get_site_user")({"ignore_auth": True}, {})
    context = {"model": model, "session": model.Session, "user": user["name"]}
    try:
        logic.check_access("datastore_delete", context)
        logic.check_access("resource_show", context)
    except logic.NotAuthorized:
        print("User is not authorized to perform this action.")
        sys.exit(1)

    files_to_keep = self._cleanup_storage_files(context, resource_path)
    _delete_orphaned_storage_directories(resource_path)
    print("{} Files are remaining in storage".format(len(files_to_keep)))


def _get_datastore_table_page(self, context, offset=0):
    # query datastore to get all resources from the _table_metadata
    result = logic.get_action("datastore_search")(
        context, {"resource_id": "_table_metadata", "offset": offset}
    )

    resource_id_list = []
    for record in result["records"]:
        try:
            # ignore 'alias' records
            if record["alias_of"]:
                continue

            logic.check_access("resource_show", context)
            logic.get_action("resource_show")(context, {"id": record["name"]})
            print("Resource '%s' found" % record["name"])
        except logic.NotFound:
            resource_id_list.append(record["name"])
            print("Resource '%s' *not* found" % record["name"])
        except logic.NotAuthorized:
            print("User is not authorized to perform this action.")
        except (KeyError, AttributeError) as e:
            print("Error while handling record %s: %s" % (record, str(e)))
            continue

    # are there more records?
    has_next_page = len(result["records"]) > 0

    return resource_id_list, has_next_page


def _cleanup_storage_files(self, context, resource_path):
    files_to_delete = []
    files_to_keep = []
    for root, dirs, files in os.walk(resource_path, topdown=True):
        if files:
            for file in files:
                resource_id = "".join(root.split("/")[-2:]) + file
                file_path = os.path.join(root, file)
                try:
                    logic.check_access("resource_show", context)
                    logic.get_action("resource_show")(context, {"id": resource_id})
                    files_to_keep.append(file_path)
                except logic.NotFound:
                    files_to_delete.append(file_path)
                except logic.NotAuthorized:
                    print("User is not authorized to perform this action.")
                    sys.exit(1)
                except (KeyError, AttributeError) as e:
                    raise RuntimeError(
                        "Error while handling record {}: {}".format(
                            resource_id, str(e)
                        )
                    )
    print("{} files will be deleted:".format(len(files_to_delete)))
    for file_path in files_to_delete:
        os.remove(file_path)
        print("- deleted: {}".format(file_path))
    return files_to_keep


def _get_resource_storage_path():
    """get resource storage path"""
    try:
        storage_path = get_storage_path()
    except Exception as e:
        print("Error occurred while getting" "storage path configuration: {}".format(e))
        sys.exit(1)
    else:
        return os.path.join(storage_path, "resources")


def _delete_orphaned_storage_directories(resource_path):
    """delete orphaned storage directories"""
    dirs_to_delete = []
    for dir in os.listdir(resource_path):
        dir_path = os.path.join(resource_path, dir)
        subdirs = os.listdir(dir_path)
        dir_empty = True
        for subdir in subdirs:
            subdir_path = os.path.join(dir_path, subdir)
            if not os.listdir(subdir_path):
                dirs_to_delete.append(subdir_path)
            else:
                dir_empty = False
        if dir_empty:
            dirs_to_delete.append(dir_path)
    print("{} directories will be deleted:".format(len(dirs_to_delete)))
    for dir_path in dirs_to_delete:
        os.rmdir(dir_path)
        print("- deleted {}".format(dir_path))
