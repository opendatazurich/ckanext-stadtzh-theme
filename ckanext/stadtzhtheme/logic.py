import pysolr
import re
from unidecode import unidecode
from ckan.plugins.toolkit import get_or_bust, side_effect_free
from ckan.logic import ActionError, NotFound, ValidationError
from ckan.lib.search.common import make_connection

import logging
log = logging.getLogger(__name__)


@side_effect_free
def ogdzh_autosuggest(context, data_dict):
    q = get_or_bust(data_dict, 'q')
    fq = data_dict.get('fq', '')

    if fq:
        fq = 'NOT private AND %s' % fq
    else:
        fq = 'NOT private'

    handler = '/suggest'
    suggester = 'default'

    solr = make_connection()
    try:
        log.debug(
            'Loading suggestions for %s (fq: %s)' % (q, fq)
        )
        results = solr.search(
            '',
            search_handler=handler,
            **{'suggest.q': q, 'suggest.count': 10, 'suggest.cfq': fq}
        )
        suggestions = results.raw_response['suggest'][suggester].values()[0]  # noqa
        terms = list(set([suggestion['term']
                 for suggestion in suggestions['suggestions']]))
        log.debug("terms {}".format(terms))
        return list(set(terms))
    except pysolr.SolrError as e:
        log.exception('Could not load suggestions from solr: %s' % e)
    raise ActionError('Error retrieving suggestions from solr')