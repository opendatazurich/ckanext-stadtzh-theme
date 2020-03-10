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

## Logic for Autosuggestion

This extension currently provides one action to collect autosuggestions
from the solr handler `/suggest`: 
The action is `ogdzh_autosuggest` with the paramters:

 - `q`: the search term 
 - `cfq`: the context: possible context are all facet names. They can be added using `AND`.   

Here are some examples for api calls to get the autosuggestions:
```
http://stadtzh.lo/api/3/action/ogdzh_autosuggest?q=velo&cfq=geodaten AND csv
http://stadtzh.lo/api/3/action/ogdzh_autosuggest?q=velo&cfq=geodaten
http://stadtzh.lo/api/3/action/ogdzh_autosuggest?q=velo&cfq=jpeg
```

The logic will only work if solr has generated autosuggestions. 
This can be tested with the command:
```
http://stadtzh.lo:8983/solr/ckan/suggest?wt=json&suggest.count=100&suggest.q=velo
```

### Remarks

- When facets are added in the future ogdzh_autocomplete.js must be adapted 
  to filter for these facets in its context search.
