ckanext-stadtzh-theme
=====================

Theme for the [Open Data Portal for the City of Zurich](https://data.stadt-zuerich.ch/).

## Command

This extension currently provides one paster command, to cleanup the datastore database.
[Datastore currently does not delete tables](https://github.com/ckan/ckan/issues/3422) when the corresponding resource is deleted.
This command finds these orphaned tables and deletes its rows to free the space in the database.
It is meant to be run regularly by a cronjob.

```bash
paster --plugin=ckanext-stadtzh-theme stadtzhtheme cleanup_datastore -c /etc/ckan/default/development.ini
```
