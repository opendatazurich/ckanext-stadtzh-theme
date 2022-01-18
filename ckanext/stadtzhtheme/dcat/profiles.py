# -*- coding: utf-8 -*-

from ckanext.dcat.profiles import RDFProfile, SchemaOrgProfile
from ckanext.dcat.utils import resource_uri
from ckan.lib.helpers import url_for, render_markdown
import ckanext.stadtzhtheme.plugin as plugin

import datetime
from dateutil.parser import parse as parse_date
from rdflib import URIRef, BNode, Literal
from rdflib.namespace import Namespace, RDF, XSD, SKOS, RDFS

import itertools
import pylons
import traceback
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
    'cc-by': 'NonCommercialAllowed-CommercialAllowed-ReferenceRequired',
    'cc-zero': 'NonCommercialAllowed-CommercialAllowed-ReferenceNotRequired',
}

mapping_accrualPeriodicity = {
    'halbjaehrlich': 'http://purl.org/cld/freq/semiannual',
    'jaehrlich': 'http://purl.org/cld/freq/annual',
    'laufend': 'http://purl.org/cld/freq/continuous',
    'monatlich': 'http://purl.org/cld/freq/monthly',
    'quartalsweise': 'http://purl.org/cld/freq/quarterly',
    'stuendlich': 'http://purl.org/cld/freq/continuous',
    'taeglich': 'http://purl.org/cld/freq/daily',
    'woechentlich': 'http://purl.org/cld/freq/weekly',
    'vierzehntäglich': 'http://purl.org/cld/freq/bimonthly',
    'keines': 'http://purl.org/cld/freq/irregular',
    'alle 4 Jahre': 'http://purl.org/cld/freq/irregular',
    'sporadisch oder unregelmaessig':
        'http://purl.org/cld/freq/irregular',
}

ckan_locale_default = pylons.config.get('ckan.locale_default', 'de')


class StadtzhProfile(object):
    def _rights(self, ckan_license_id):
        return mapping_rights_dict.get(ckan_license_id)

    def _themes(self, group_id):
        return mapping_groups_dict.get(group_id, [])

    def _time_interval_from_dataset(self, dataset_dict):
        time_range = self._get_dataset_value(dataset_dict, 'timeRange')
        if time_range is None:
            return None
        time_interval = {}
        try:
            dates = time_range.encode('utf-8').strip().split('-', 1)
            dates = [d.strip() for d in dates]
            if len(dates) > 0 and dates[0].isdigit() and len(dates[0]) == 4:
                time_interval['start_date'] = dates[0] + '-01-01'
                if len(dates) > 1 and dates[1].isdigit() and len(dates[1]) == 4:  # noqa
                    end_year = dates[1]
                else:
                    end_year = dates[0]
                time_interval['end_date'] = end_year + '-12-31'
            else:
                return None
        except (TypeError, IndexError):
            return None

        return time_interval


class StadtzhSwissDcatProfile(RDFProfile, StadtzhProfile):
    def _add_date_triple(self, subject, predicate, value, _type=Literal):
        '''
        Adds a new triple with a date object
        Dates are parsed using dateutil, and if the date obtained is correct,
        added to the graph as an XSD.dateTime value.
        If there are parsing errors, the literal string value is added.
        '''
        if not value:
            return
        try:
            default_datetime = datetime.datetime(1, 1, 1, 0, 0, 0)
            _date = parse_date(value, default=default_datetime, dayfirst=True)

            self.g.add((subject, predicate, _type(_date.isoformat(),
                                                  datatype=XSD.dateTime)))
        except ValueError:
            self.g.add((subject, predicate, _type(value)))

    def graph_from_dataset(self, dataset_dict, dataset_ref):  # noqa: C90
        try:

            g = self.g

            g.add((dataset_ref, RDF.type, DCAT.Dataset))

            for prefix, namespace in namespaces.iteritems():
                g.bind(prefix, namespace)

            # Basic fields
            basic_items = [
                ('version', OWL.versionInfo, ['dcat_version'], Literal),
            ]
            self._add_triples_from_dict(dataset_dict, dataset_ref, basic_items)

            # landingPage is the original portal page
            site_url = pylons.config.get('ckan.site_url', '')
            g.add((
                dataset_ref,
                DCAT.landingPage,
                Literal(site_url + '/dataset/' + dataset_dict['name'])
            ))

            # Language
            g.add((dataset_ref, DCT.language, Literal(ckan_locale_default)))

            # Basic date fields
            date_items = [
                ('dateLastUpdated', DCT.modified, 'metadata_modified', Literal),  # noqa
                ('dateFirstPublished', DCT.issued, 'metadata_created', Literal),  # noqa
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
                accrualPeriodicity = mapping_accrualPeriodicity.get(
                    update_interval[0]
                )
            except IndexError:
                accrualPeriodicity = None
            if accrualPeriodicity:
                g.add((
                    dataset_ref,
                    DCT.accrualPeriodicity,
                    URIRef(accrualPeriodicity)
                ))

            # Temporal
            time_range = self._time_interval_from_dataset(dataset_dict)
            if time_range is not None and time_range.get('start_date') and time_range.get('end_date'):  # noqa
                start = time_range.get('start_date')
                end = time_range.get('end_date')

                temporal_extent = BNode()
                g.add((temporal_extent, RDF.type, DCT.PeriodOfTime))
                g.add((
                    temporal_extent,
                    SCHEMA.startDate,
                    Literal(start, datatype=XSD.date)
                ))
                g.add((
                    temporal_extent,
                    SCHEMA.endDate,
                    Literal(end, datatype=XSD.date)
                ))
                g.add((dataset_ref, DCT.temporal, temporal_extent))

            # Themes
            groups = self._get_dataset_value(dataset_dict, 'groups')
            try:
                theme_names = set(itertools.chain.from_iterable(
                    [self._themes(group.get('name')) for group in
                     groups]))
                if any(tag['name'] == 'geodaten'
                       for tag in dataset_dict.get('tags', [])):
                    theme_names.add('geography')

                for theme_name in theme_names:
                    g.add((
                        dataset_ref,
                        DCAT.theme,
                        URIRef(ogd_theme_base_url + theme_name)
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
                g.add((contact_details, VCARD.hasEmail, URIRef(maintainer_email)))  # noqa

                items = [
                    ('contact_name', VCARD.fn, ['maintainer', 'author'], Literal),  # noqa
                ]
                self._add_triples_from_dict(dataset_dict, contact_details, items)   # noqa

            # Tags
            for tag in dataset_dict.get('tags', []):
                g.add((
                    dataset_ref,
                    DCAT.keyword,
                    Literal(tag['name'], lang=ckan_locale_default)
                ))

            # Resources
            for resource_dict in dataset_dict.get('resources', []):
                distribution = URIRef(resource_uri(resource_dict))

                g.add((dataset_ref, DCAT.distribution, distribution))
                g.add((distribution, RDF.type, DCAT.Distribution))
                g.add((distribution, DCT.language, Literal(ckan_locale_default)))  # noqa

                #  Simple values
                items = [
                    ('id', DCT.identifier, None, Literal),
                    ('name', DCT.title, None, Literal),
                    ('description', DCT.description, None, Literal),
                    ('state', ADMS.status, None, Literal),
                ]

                self._add_triples_from_dict(resource_dict, distribution, items)

                license_id = self._get_dataset_value(dataset_dict, 'license_id')  # noqa
                license_title = self._rights(license_id)
                g.add((distribution, DCT.rights, Literal(license_title)))
                g.add((distribution, DCT.license, Literal(license_title)))

                #  Lists
                items = [
                    ('conforms_to', DCT.conformsTo, None, Literal),
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
                    ('created', DCT.issued, None, Literal),
                    ('last_modified', DCT.modified, None, Literal),
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
        except Exception, e:
            log.exception(
                "Something went wrong: %s / %s" % (e, traceback.format_exc())
            )
            raise

    def graph_from_catalog(self, catalog_dict, catalog_ref):
        g = self.g
        g.add((catalog_ref, RDF.type, DCAT.Catalog))


class StadtzhSchemaOrgProfile(SchemaOrgProfile, StadtzhProfile):
    def additional_fields(self, dataset_ref, dataset_dict):
        # identifier
        dataset_url = url_for('dataset_read',
                              id=dataset_dict['name'],
                              qualified=True)
        self.g.add((dataset_ref, SCHEMA.identifier, Literal(dataset_url)))

        # text
        bemerkungen = render_markdown(dataset_dict.get('sszBemerkungen', ''))
        self.g.add((dataset_ref, SCHEMA.text, Literal(bemerkungen)))

        # description (render markdown)
        notes = render_markdown(dataset_dict.get('notes', ''))
        self.g.remove((dataset_ref, SCHEMA.description, None))
        self.g.add((dataset_ref, SCHEMA.description, Literal(notes)))

        # sourceOrganization
        author = dataset_dict.get('author', '')
        self.g.add((dataset_ref, SCHEMA.sourceOrganization, Literal(author)))

        # author
        data_publisher = dataset_dict.get('data_publisher', '')
        self.g.add((dataset_ref, SCHEMA.author, Literal(data_publisher)))

        # spatialRelationship
        spatial = dataset_dict.get('spatialRelationship', '')
        if spatial:
            # add spatialRelationship as literal ("named location")
            self.g.add((dataset_ref, SCHEMA.spatialCoverage, Literal(spatial)))

    def _temporal_graph(self, dataset_ref, dataset_dict):
        time_range = self._time_interval_from_dataset(dataset_dict)
        if time_range is not None and time_range.get('start_date') and time_range.get('end_date'):  # noqa
            start = time_range.get('start_date')
            end = time_range.get('end_date')
            if start and end:
                self.g.add((dataset_ref, SCHEMA.temporalCoverage, Literal('%s/%s' % (start, end))))  # noqa
            elif start:
                self._add_date_triple(dataset_ref, SCHEMA.temporalCoverage, start)  # noqa
            elif end:
                self._add_date_triple(dataset_ref, SCHEMA.temporalCoverage, end)  # noqa

    def _distribution_url_graph(self, distribution, resource_dict):
        url = resource_dict.get('url')
        res_type = resource_dict.get('resource_type')
        if url and res_type == 'file':
            self.g.add((distribution, SCHEMA.contentUrl, Literal(url)))
        if url:
            self.g.add((distribution, SCHEMA.url, Literal(url)))

        theme_plugin = plugin.StadtzhThemePlugin()
        descriptions = theme_plugin.get_resource_descriptions(resource_dict)
        description = render_markdown(" ".join(descriptions))
        self.g.add((distribution, SCHEMA.description, Literal(description)))
