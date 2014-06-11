from setuptools import setup, find_packages
import sys, os

version = '0.0'

setup(
    name='ckanext-stadtzh_theme',
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
    namespace_packages=['ckanext', 'ckanext.stadtzh_theme'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    entry_points=
    """
    [ckan.plugins]
    stadtzh_theme=ckanext.stadtzh_theme.plugin:StadtzhThemePlugin
    """,
)
