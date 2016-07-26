from ckanext.dcat.profiles import RDFProfile
from ckanext.dcat.utils import resource_uri, publisher_uri_from_dataset_dict

import rdflib
from rdflib import URIRef, BNode, Literal
from rdflib.namespace import Namespace, RDF, XSD, SKOS, RDFS

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
ODRS = Namespace('http://schema.theodi.org/odrs#')

GEOJSON_IMT = 'https://www.iana.org/assignments/media-types/application/vnd.geo+json'

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
    'odrs': ODRS,
}



class StadtzhSwissDcatProfile(RDFProfile):

    def graph_from_dataset(self, dataset_dict, dataset_ref):

        g = self.g

        catalog_node = URIRef("http://example.org/Catalog")
        dataset_node = URIRef("http://example.org/dataset")  # dcat:Dataset
        g.add((catalog_node, RDF.type, DCAT.Catalog))
        g.add((catalog_node, DCAT.dataset, dataset_node))
        g.add((dataset_node, RDF.type, DCAT.Dataset))

        # self.add((dataset_dict, catalog_ref, DCAT.dataset)) !!!!

        for prefix, namespace in namespaces.iteritems():
            g.bind(prefix, namespace)

        # Basic fields
        basic_items = [
            ('title', DCT.title, None),
            ('notes', DCT.description, None),
            ('url', DCAT.landingPage, None),
            ('identifier', DCT.identifier, ['guid', 'id']),
            # ('version', OWL.versionInfo, ['dcat_version']),
            # ('version_notes', ADMS.versionNotes, None),
            # ('frequency', DCT.accrualPeriodicity, None),
            # ('data_publisher', DCT.publisher, None),
            ('metadata_modified', DCT.modified, None),
            # ('maintainer_email', DCAT.contactPoint, None),
        ]

        self._add_triples_from_dict(dataset_dict, dataset_node, basic_items)

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

            contact_uri = self._get_dataset_value(dataset_dict, 'contact_uri')
            if contact_uri:
                contact_details = URIRef(contact_uri)
            else:
                contact_details = BNode()

            g.add((contact_details, RDF.type, VCARD.Organization))
            g.add((dataset_node, DCAT.contactPoint, contact_details))

            items = [
                ('contact_name', VCARD.fn, ['maintainer', 'author']),
                ('contact_email', VCARD.hasEmail, ['maintainer_email',
                                                   'author_email']),
            ]

            self._add_triples_from_dict(dataset_dict, contact_details, items)

        # Resources
        for resource_dict in dataset_dict.get('resources', []):

            # distribution = URIRef(resource_uri(resource_dict))
            distribution = BNode()

            g.add((dataset_node, DCAT.distribution, distribution))
            g.add((distribution, RDF.type, DCAT.Distribution))


            #  Simple values
            items = [
                ('name', DCT.title, None),
                ('description', DCT.description, None),
                ('status', ADMS.status, None),
                ('rights', DCT.rights, None),
                ('license', DCT.license, None),
            ]

            self._add_triples_from_dict(resource_dict, distribution, items)

            #  Lists
            items = [
                ('documentation', FOAF.page, None),
                ('language', DCT.language, None),
                ('conforms_to', DCT.conformsTo, None),
            ]
            self._add_list_triples_from_dict(resource_dict, distribution, items)

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

            # URL
            url = resource_dict.get('url')
            download_url = resource_dict.get('download_url')
            if download_url:
                g.add((distribution, DCAT.downloadURL, Literal(download_url)))
            if (url and not download_url) or (url and url != download_url):
                g.add((distribution, DCAT.accessURL, Literal(url)))

            # Dates
            items = [
                ('issued', DCT.issued, None),
                ('modified', DCT.modified, None),
            ]

            self._add_date_triples_from_dict(resource_dict, distribution, items)

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
        if any([
            self._get_dataset_value(dataset_dict, 'publisher_uri'),
            self._get_dataset_value(dataset_dict, 'publisher_name'),
            dataset_dict.get('organization'),
        ]):

            publisher_uri = publisher_uri_from_dataset_dict(dataset_dict)
            # if publisher_uri:
            #     publisher_details = URIRef(publisher_uri)
            # else:
            #     # No organization nor publisher_uri
            #     publisher_details = BNode()
            publisher_details = BNode()

            g.add((publisher_details, RDF.type, RDF.Description))
            # g.add((dataset_node, DCT.publisher, publisher_details))
            g.add((dataset_node, DCT.publisher, publisher_details))

            publisher_name = self._get_dataset_value(dataset_dict, 'publisher_name')
            if not publisher_name and dataset_dict.get('organization'):
                publisher_name = dataset_dict['organization']['title']

            g.add((publisher_details, RDFS.label, Literal(publisher_name)))
            # TODO: It would make sense to fallback these to organization
            # fields but they are not in the default schema and the
            # `organization` object in the dataset_dict does not include
            # custom fields
            items = [
                ('publisher_email', FOAF.mbox, None),
                ('publisher_url', FOAF.homepage, None),
                ('publisher_type', DCT.type, None),
            ]

            self._add_triples_from_dict(dataset_dict, publisher_details, items)