import pysolr
import re
from unidecode import unidecode
from ckan.plugins.toolkit import get_or_bust, side_effect_free
from ckan.logic import ActionError, NotFound, ValidationError
from ckan.lib.search.common import make_connection
import ckan.plugins.toolkit as tk

import logging
log = logging.getLogger(__name__)


@side_effect_free
def ogdzh_autosuggest(context, data_dict):
    q = get_or_bust(data_dict, 'q')
    cfq = data_dict.get('cfq', '')

    if cfq:
        cfq = 'active AND %s' % cfq
    else:
        cfq = 'active'

    handler = '/suggest'
    suggester = 'default'

    try:
        suggest_limit = tk.config.get('ckanext.stadtzh-theme.ogdzh_autosuggest_limit')
    except:
        suggest_limit = 100

    solr = make_connection()
    try:
        log.debug(
            'Loading suggestions for %s (cfq: %s)' % (q, cfq)
        )
        results = solr.search(
            '',
            search_handler=handler,
            **{'suggest.q': q, 'suggest.count': suggest_limit, 'suggest.cfq': cfq}
        )
        suggestions = results.raw_response['suggest'][suggester].values()[0]  # noqa
        terms = list(set([suggestion['term']
                 for suggestion in suggestions['suggestions']]))
        log.debug("terms {}".format(terms))
        return list(set(terms))
    except pysolr.SolrError as e:
        log.exception('Could not load suggestions from solr: %s' % e)
    raise ActionError('Error retrieving suggestions from solr')