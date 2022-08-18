# --- core imports
import logging
import os
import re
import xml.etree.ElementTree as xm
from time import sleep

import pandas as pd
import requests
import requests as rq

# ---application imports
from requests import Request

from geo_to_hca.utils import handle_errors

# --- third-party imports

"""
Define constants.
"""
STATUS_ERROR_CODE = 400

"""
Functions to handle requests from NCBI SRA database or NCBI eutils.
"""


NCBI_WEB_HOST=os.getenv('EUTILS_HOST', default='https://www.ncbi.nlm.nih.gov')
EUTILS_HOST=os.getenv('EUTILS_HOST', default='https://eutils.ncbi.nlm.nih.gov')
EUTILS_BASE_URL=os.getenv('EUTILS_BASE_URL', default=f'{EUTILS_HOST}/entrez/eutils')
log = logging.getLogger(__name__)


def get_srp_accession_from_geo(geo_accession: str) -> [str]:
    """
    Function to retrieve any SRA database study accessions for a given input GEO accession.
    """
    regex = re.compile('^GSE.*$')
    if not regex.match(geo_accession):
        raise AssertionError(f'{geo_accession} is not a valid GEO accession')

    try:
        default_params = {
            'db': 'gds',
            'retmode': 'json'
        }

        r = requests.get(f'{EUTILS_BASE_URL}/esearch.fcgi',
                         params={**default_params, 'term': geo_accession})
        r.raise_for_status()

        for summary_id in r.json()['esearchresult']['idlist']:
            sleep(0.5)  # Have to sleep so don't cause 429 error. Limit is 3/second
            r = requests.get(f'{EUTILS_BASE_URL}/esummary.fcgi',
                             params={**default_params, 'id': summary_id})
            r.raise_for_status()

            related_study = find_related_study(geo_accession, r)
            return related_study

    except Exception as e:
        raise Exception(f'Failed to get SRP accessions for GEO accession {geo_accession}: {e}')


def find_related_study(geo_accession, esummary_response):
    results = [x for x in esummary_response.json()['result'].values() if type(x) is dict]
    extrelations = [x for x in [x.get('extrelations') for x in results] for x in x]
    related_studies = [relation['targetobject'] for relation in extrelations if 'SRP' in relation.get('targetobject', '')]
    if not related_studies:
        raise ValueError(f"Could not find an SRA study associated with Geo accession {geo_accession}. "
                         f"Go to {NCBI_WEB_HOST}/geo/query/acc.cgi?acc={geo_accession} and check if a study is "
                         f"linked to a sample via an experiment (SRX...). You could use that study with the "
                         f"geo-to-hca tool.")
    if len(related_studies) > 1:
        raise ValueError(f"More than a single accession has been found associated with Geo accession {geo_accession}")
    return related_studies[0]


def get_srp_metadata(srp_accession: str) -> pd.DataFrame:
    """
    Function to retrieve a dataframe with multiple lists of experimental and sample accessions
    associated with a particular SRA study accession from the SRA database.
    """
    sleep(0.5)
    esearch_result = get_entrez_esearch(srp_accession)
    efetch_request = Request(method='GET',
                             url=f'{EUTILS_BASE_URL}/efetch.fcgi',
                             params={
                                 "db": "sra",
                                 "query_key": esearch_result['querykey'],
                                 "WebEnv": esearch_result['webenv'],
                                 "rettype": "runinfo",
                                 "retmode": "text",
                             }).prepare()
    log.debug(f'srp_metadata url: {efetch_request.url}')
    return pd.read_csv(efetch_request.url)


def get_entrez_esearch(srp_accession):
    r = requests.get(url=f'{EUTILS_BASE_URL}/esearch.fcgi',
                     params={
                         "db": "sra",
                         "term": srp_accession,
                         "usehistory": "y",
                         "format": "json",
                     })
    log.debug(f'esearch url:  {r.url}')
    log.debug(f'esearch response status:  {r.status_code}')
    log.debug(f'esearch response content:  {r.text}')
    r.raise_for_status()
    return r.json()['esearchresult']


def parse_xml_SRA_runs(xml_content: object) -> object:
    for experiment_package in xml_content.findall('EXPERIMENT_PACKAGE'):
        yield experiment_package


def request_fastq_from_SRA(srr_accessions: []) -> object:
    """
    Function to retrieve an xml file containing information associated with a list of NCBI SRA run accessions.
    In particular, the xml contains the paths to the data (if available) in fastq or other format.
    """
    sleep(0.5)
    esearch_result = get_entrez_esearch(",".join(srr_accessions))
    srr_metadata_url = rq.get(f'{EUTILS_BASE_URL}/efetch/fcgi',
                              params={
                                  "db": "sra",
                                  "WebEnv": esearch_result['webenv'],
                                  "query_key": esearch_result['querykey'],
                                  "id": ",".join(srr_accessions)
                              })
    if srr_metadata_url.status_code == STATUS_ERROR_CODE:
        raise handle_errors.NotFoundSRA(srr_metadata_url, srr_accessions)
    try:
        xml_content = xm.fromstring(srr_metadata_url.content)
    except:
        xml_content = None
    return xml_content


def request_accession_info(accessions: [], accession_type: str) -> object:
    """
    Function which sends a request to NCBI SRA database to get an xml file with metadata about a
    given list of biosample or experiment accessions. The xml contains various metadata fields.
    """
    if accession_type == 'biosample':
        url = f'{EUTILS_BASE_URL}/efetch/fcgi?db=biosample&id={",".join(accessions)}'
    if accession_type == 'experiment':
        url = f'{EUTILS_BASE_URL}/efetch/fcgi?db=sra&id={",".join(accessions)}'
    sra_url = rq.get(url)
    if sra_url.status_code == STATUS_ERROR_CODE:
        raise handle_errors.NotFoundSRA(sra_url, accessions)
    return xm.fromstring(sra_url.content)


def request_bioproject_metadata(bioproject_accession: str):
    """
    Function to request metadata at the project level given an SRA Bioproject accession.
    """
    sleep(0.5)
    srp_bioproject_url = rq.get(
        f'{EUTILS_BASE_URL}/efetch/fcgi?db=bioproject&id={bioproject_accession}')
    if srp_bioproject_url.status_code == STATUS_ERROR_CODE:
        raise handle_errors.NotFoundSRA(srp_bioproject_url, bioproject_accession)
    return xm.fromstring(srp_bioproject_url.content)


def request_pubmed_metadata(project_pubmed_id: str):
    """
    Function to request metadata at the publication level given a pubmed ID.
    """
    sleep(0.5)
    pubmed_url = rq.get(
        f'{EUTILS_BASE_URL}/efetch/fcgi?db=pubmed&id={project_pubmed_id}&rettype=xml')
    if pubmed_url.status_code == STATUS_ERROR_CODE:
        raise handle_errors.NotFoundSRA(pubmed_url, project_pubmed_id)
    return xm.fromstring(pubmed_url.content)
