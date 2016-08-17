from ckanext.dcat.profiles import RDFProfile
from ckanext.dcat.utils import resource_uri, publisher_uri_from_dataset_dict

import rdflib
from rdflib import URIRef, BNode, Literal
from rdflib.namespace import Namespace, RDF, XSD, SKOS, RDFS

import pylons
import logging
log = logging.getLogger(__name__)


DCT = Namespace("http://purl.org/dc/terms/")
DCAT = Namespace("http://www.w3.org/ns/dcat#")
ADMS = Namespace("http://www.w3.org/ns/adms#")
VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
SCHEMA = Namespace('http://schema.org/')
TIME = Namespace('http://www.w3.org/2006/time')
LOCN = Namespace('http://www.w3.org/ns/locn#')
GSP = Namespace('http://www.opengis.net/ont/geosparql#')
OWL = Namespace('http://www.w3.org/2002/07/owl#')
SPDX = Namespace('http://spdx.org/rdf/terms#')
XML = Namespace('http://www.w3.org/2001/XMLSchema')

namespaces = {
    'dct': DCT,
    'dcat': DCAT,
    'adms': ADMS,
    'vcard': VCARD,
    'foaf': FOAF,
    'schema': SCHEMA,
    'time': TIME,
    'skos': SKOS,
    'locn': LOCN,
    'gsp': GSP,
    'owl': OWL,
    'xml': XML,
}

ogd_theme_base_url = 'http://opendata.swiss/themes/'
mapping_groups_dict = {
    'arbeit-und-erwerb': ['work'],
    'finanzen': ['finances'],
    'preise': ['prices'],
    'tourismus': ['tourism'],
    'volkswirtschaft': ['national-economy'],
    'wirtschaft': ['national-economy'],
    'verwaltung': ['administration'],
    'soziales': ['social-security'],
    'freizeit': ['territory'],
    'umwelt': ['territory'],
    'politik': ['politics'],
    'mobilitat': ['mobility'],
    'kultur': ['culture'],
    'kriminalitat': ['crime', 'public-order'],
    'gesundheit': ['health'],
    'basiskarten': ['territory', 'geography'],
    'energie': ['energy'],
    'bildung': ['education'],
    'bevolkerung': ['population'],
    'bauen-und-wohnen': ['construction'],
}
mapping_rights_dict = {
    'cc-by-sa': 'NonCommercialAllowed-CommercialAllowed-ReferenceRequired',
    'cc-zero': 'NonCommercialAllowed-CommercialAllowed-ReferenceNotRequired',
}

# Values 'sporadisch oder unregelmaessig' and 'keines'
# do not have an equivalent in OGD and are ignored
mapping_accrualPerdiodicty = {
    'halbjaehrlich': 'http://purl.org/cld/freq/semiannual',
    'jaehrlich': 'http://purl.org/cld/freq/annual',
    'laufend': 'http://purl.org/cld/freq/continuous',
    'monatlich': 'http://purl.org/cld/freq/monthly',
    'quartalsweise': 'http://purl.org/cld/freq/quarterly',
    'stuendlich': 'http://purl.org/cld/freq/continuous',
    'taeglich': 'http://purl.org/cld/freq/daily',
    'woechentlich': 'http://purl.org/cld/freq/weekly',
    'keines': 'http://purl.org/cld/freq/completelyIrregular',
    'sporadisch oder unregelmaessig':
        'http://purl.org/cld/freq/completelyIrregular',
}

ckan_locale_default = pylons.config.get('ckan.locale_default', 'de')

class StadtzhSwissDcatProfile(RDFProfile):

    def _rights(self, ckan_license_id):
        return mapping_rights_dict.get(ckan_license_id)

    def _themes(self, group_id):
        return mapping_groups_dict.get(group_id, [])

    def _time_interval(self, dataset_dict):
        time_range = self._get_dataset_value(dataset_dict, 'timeRange')
        if time_range is None:
            return None
        time_interval = {}
        try:
            dates = time_range.encode('utf-8').strip().split('-', 1)
            if len(dates) > 0 and dates[0].isdigit() and len(dates[0]) == 4:
                time_interval['start_date'] = dates[0] + '-01-01'
                if len(dates) > 1 and dates[1].isdigit() and len(dates[1] == 4):
                    end_year = dates[1]
                else:
                    end_year = dates[0]
                time_interval['end_date'] = end_year + '-12-31'
            else:
                return None
        except (TypeError, IndexError):
            return None

        return time_interval

    def graph_from_dataset(self, dataset_dict, dataset_ref):

        g = self.g

        g.add((dataset_ref, RDF.type, DCAT.Dataset))

        for prefix, namespace in namespaces.iteritems():
            g.bind(prefix, namespace)

        # Basic fields
        basic_items = [
            ('version', OWL.versionInfo, ['dcat_version']),
        ]
        self._add_triples_from_dict(dataset_dict, dataset_ref, basic_items)

        # landingPage is the original portal page
        site_url = pylons.config.get('ckan.site_url', '')
        g.add((dataset_ref, DCAT.landingPage, Literal(site_url + '/dataset/' + dataset_dict['name'])))

        # Language
        g.add((dataset_ref, DCT.language, Literal(ckan_locale_default)))

        # Basic date fields
        date_items = [
            ('metadata_modified', DCT.modified, None),
            ('metadata_created', DCT.issued, None),
        ]
        self._add_date_triples_from_dict(
            dataset_dict,
            dataset_ref,
            date_items
        )

        # Organization
        organization_id = pylons.config.get(
            'ckanext.stadtzh-theme.dcat_ap_organization_slug',
            '',
        )
        id = self._get_dataset_value(dataset_dict, 'id')
        title = self._get_dataset_value(dataset_dict, 'title')
        description = self._get_dataset_value(dataset_dict, 'notes')
        g.add((
            dataset_ref,
            DCT.identifier,
            Literal(id + '@' + organization_id)
        ))
        g.add((
            dataset_ref,
            DCT.title,
            Literal(title, lang=ckan_locale_default)
        ))
        g.add((
            dataset_ref,
            DCT.description,
            Literal(description, lang=ckan_locale_default)
        ))

        # Update Interval
        try:
            update_interval = self._get_dataset_value(
                dataset_dict,
                'updateInterval'
            )
            accrualPeriodicity = mapping_accrualPerdiodicty.get(update_interval[0])
        except IndexError:
            accrualPeriodicity = None
        if accrualPeriodicity:
            g.add((
                dataset_ref,
                DCT.accrualPeriodicity,
                URIRef(accrualPeriodicity)
            ))

        # Temporal
        time_range = self._time_interval(dataset_dict)
        if time_range is not None and time_range.get('start_date') and time_range.get('end_date'):
            start = time_range.get('start_date')
            end = time_range.get('end_date')

            temporal_extent = BNode()
            g.add((temporal_extent, RDF.type, DCT.PeriodOfTime))
            g.add((temporal_extent, SCHEMA.startDate, Literal(start,
                                                    datatype=XSD.date)))
            g.add((temporal_extent, SCHEMA.endDate, Literal(end,
                                                    datatype=XSD.date)))
            g.add((dataset_ref, DCT.temporal, temporal_extent))

        # Themes
        groups = self._get_dataset_value(dataset_dict, 'groups')
        try:
            group_id = groups[0].get('id')
            theme_ids = self._themes(group_id)
            for theme_id in theme_ids:
                g.add((
                    dataset_ref,
                    DCAT.theme,
                    URIRef(ogd_theme_base_url + theme_id)
                ))
        except IndexError:
            pass

        # Legal Information
        legal_information = self._get_dataset_value(
            dataset_dict,
            'legalInformation'
        )
        g.add((dataset_ref, DCT.accessRights, Literal(legal_information)))

        # Contact details
        if any([
            self._get_dataset_value(dataset_dict, 'contact_uri'),
            self._get_dataset_value(dataset_dict, 'contact_name'),
            self._get_dataset_value(dataset_dict, 'contact_email'),
            self._get_dataset_value(dataset_dict, 'maintainer'),
            self._get_dataset_value(dataset_dict, 'maintainer_email'),
            self._get_dataset_value(dataset_dict, 'author'),
            self._get_dataset_value(dataset_dict, 'author_email'),
        ]):

            contact_details = BNode()

            g.add((contact_details, RDF.type, VCARD.Organization))
            g.add((dataset_ref, DCAT.contactPoint, contact_details))

            maintainer_email = self._get_dataset_value(
                dataset_dict,
                'maintainer_email'
            )
            g.add((contact_details, VCARD.hasEmail, URIRef(maintainer_email)))

            items = [
                ('contact_name', VCARD.fn, ['maintainer', 'author']),
            ]
            self._add_triples_from_dict(dataset_dict, contact_details, items)

        # Tags
        for tag in dataset_dict.get('tags', []):
            g.add((
                dataset_ref,
                DCAT.keyword,
                Literal(tag['name'], lang=ckan_locale_default)
            ))

        # Resources
        for resource_dict in dataset_dict.get('resources', []):
            distribution = BNode()

            g.add((dataset_ref, DCAT.distribution, distribution))
            g.add((distribution, RDF.type, DCAT.Distribution))

            #  Simple values
            items = [
                ('name', DCT.title, None),
                ('description', DCT.description, None),
                ('state', ADMS.status, None),
            ]

            self._add_triples_from_dict(resource_dict, distribution, items)

            license_id = self._get_dataset_value(dataset_dict, 'license_id')
            license_title = self._rights(license_id)
            g.add((distribution, DCT.rights, Literal(license_title)))
            g.add((distribution, DCT.license, Literal(license_title)))

            #  Lists
            items = [
                ('theme', DCAT.theme, None),
                ('language', DCT.language, None),
                ('conforms_to', DCT.conformsTo, None),
            ]
            self._add_list_triples_from_dict(
                resource_dict,
                distribution,
                items
            )

            # Format
            if '/' in resource_dict.get('format', ''):
                g.add((distribution, DCAT.mediaType,
                       Literal(resource_dict['format'])))
            else:
                if resource_dict.get('format'):
                    g.add((distribution, DCT['format'],
                           Literal(resource_dict['format'])))

                if resource_dict.get('mimetype'):
                    g.add((distribution, DCAT.mediaType,
                           Literal(resource_dict['mimetype'])))

            # URLs
            url = resource_dict.get('url')
            if url:
                g.add((distribution, DCAT.accessURL, Literal(url)))

            # if resource has the following format, the distribution is a
            # service and therefore doesn't need a downloadURL
            format = resource_dict.get('format').lower()
            if format not in ['xml', 'wms', 'wmts', 'wfs']:
                download_url = resource_dict.get('url')
                if download_url:
                    g.add((
                        distribution,
                        DCAT.downloadURL,
                        Literal(download_url)
                    ))

            # Dates
            items = [
                ('created', DCT.issued, None),
                ('last_modified', DCT.modified, None),
            ]

            self._add_date_triples_from_dict(
                resource_dict,
                distribution,
                items
            )

            # Numbers
            if resource_dict.get('size'):
                try:
                    g.add((distribution, DCAT.byteSize,
                           Literal(float(resource_dict['size']),
                                   datatype=XSD.decimal)))
                except (ValueError, TypeError):
                    g.add((distribution, DCAT.byteSize,
                           Literal(resource_dict['size'])))
            # Checksum
            if resource_dict.get('hash'):
                checksum = BNode()
                g.add((checksum, SPDX.checksumValue,
                       Literal(resource_dict['hash'],
                               datatype=XSD.hexBinary)))

                if resource_dict.get('hash_algorithm'):
                    if resource_dict['hash_algorithm'].startswith('http'):
                        g.add((checksum, SPDX.algorithm,
                               URIRef(resource_dict['hash_algorithm'])))
                    else:
                        g.add((checksum, SPDX.algorithm,
                               Literal(resource_dict['hash_algorithm'])))
                g.add((distribution, SPDX.checksum, checksum))

        # Publisher
        if dataset_dict.get('organization'):

            publisher_name = dataset_dict.get('author')

            publisher_details = BNode()

            g.add((publisher_details, RDF.type, RDF.Description))
            g.add((publisher_details, RDFS.label, Literal(publisher_name)))
            g.add((dataset_ref, DCT.publisher, publisher_details))

    def graph_from_catalog(self, catalog_dict, catalog_ref):
        g = self.g
        g.add((catalog_ref, RDF.type, DCAT.Catalog))
