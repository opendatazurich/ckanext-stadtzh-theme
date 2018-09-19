from setuptools import setup, find_packages

version = '0.0'

setup(
    name='ckanext-stadtzh-theme',
    version=version,
    description="CKAN theme for the City of Zurich",
    long_description="""\
    """,
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='Liip AG',
    author_email='ogd@liip.ch',
    url='http://www.liip.ch/',
    license='GPL',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext', 'ckanext.stadtzhtheme'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    entry_points=
    """
    [ckan.plugins]
    stadtzhtheme=ckanext.stadtzhtheme.plugin:StadtzhThemePlugin
    [babel.extractors]
    ckan = ckan.lib.extract:extract_ckan

    [ckan.rdf.profiles]
    stadtzh_swiss_dcat=ckanext.stadtzhtheme.dcat.profiles:StadtzhSwissDcatProfile
    stadtzh_schemaorg=ckanext.stadtzhtheme.dcat.profiles:StadtzhSchemaOrgProfile
    
    [paste.paster_command]
    stadtzhtheme=ckanext.stadtzhtheme.commands:StadtzhCommand
        
    """,
    message_extractors={
        'ckanext': [
            ('**.py', 'python', None),
            ('**.js', 'javascript', None),
            ('**/templates/**.html', 'ckan', None),
        ],
    }
)
