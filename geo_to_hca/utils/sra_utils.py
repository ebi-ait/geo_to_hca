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


NCBI_WEB_HOST=os.getenv('NCBI_WEB_HOST', default='https://www.ncbi.nlm.nih.gov')
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
        response_json = call_esearch(geo_accession, db='gds')

        for summary_id in response_json['idlist']:
            related_study = find_related_object(summary_id, accession_type='SRP')
            if related_study:
                return related_study

            for sample in find_related_samples(summary_id):
                sample_esearch_result = call_esearch(sample['accession'], db='gds')
                for sample_id in sample_esearch_result['idlist']:
                    experiment_accession = find_related_object(sample_id, accession_type='SRX')
                    if experiment_accession:
                        log.debug(f'sample {sample["accession"]} is linked to experiment {experiment_accession}')
                        related_study = find_study_by_experiment_accession(experiment_accession)
                        if related_study:
                            return related_study
        raise no_related_study_err(geo_accession)

    except Exception as e:
        raise Exception(f'Failed to get SRP accessions for GEO accession {geo_accession}: {e}')


def find_study_by_experiment_accession(experiment_accession):
    # search for accession in sra db using esearch
    experiment_esearch_result = call_esearch(experiment_accession, db='sra')
    # call esummary on sra db with the given id
    experiment_id = experiment_esearch_result['idlist'][0]
    experiment_esummary_result = call_esummary(experiment_id, db='sra')
    # read xml from expxml attribute
    experiment_xml = xm.fromstring(f"<experiment>{experiment_esummary_result['result'][experiment_id]['expxml']}</experiment>")
    related_study = experiment_xml.find('Study').attrib['acc']
    return related_study


def call_esearch(geo_accession, db='gds'):
    r = requests.get(f'{EUTILS_BASE_URL}/esearch.fcgi',
                     params={
                         'db': db,
                         'retmode': 'json',
                         'term': geo_accession})
    r.raise_for_status()
    response_json = r.json()
    return response_json['esearchresult']


def no_related_study_err(geo_accession):
    return ValueError(f"Could not find an an object with accession type SRP associated with "
                      f"the given accession {geo_accession}. "
                      f"Go to {NCBI_WEB_HOST}/geo/query/acc.cgi?acc={geo_accession} and if possible, find"
                      f"the related study accession, and run the tool with it.")


def find_related_samples(accession):
    sleep(0.5)  # Have to sleep so don't cause 429 error. Limit is 3/second
    esummary_response = requests.get(f'{EUTILS_BASE_URL}/esummary.fcgi',
                                     params={'db': 'gds',
                                             'retmode': 'json',
                                             'id': accession})
    esummary_response.raise_for_status()
    results = [x for x in esummary_response.json()['result'].values() if type(x) is dict]
    return results[0]['samples']


def find_related_object(accession, accession_type):
    sleep(0.5)  # Have to sleep so don't cause 429 error. Limit is 3/second
    esummary_response_json = call_esummary(accession, db='gds')
    results = [x for x in esummary_response_json['result'].values() if type(x) is dict]
    extrelations = [x for x in [x.get('extrelations') for x in results] for x in x]

    related_objects = [relation['targetobject'] for relation in extrelations if accession_type in relation.get('targetobject', '')]
    if not related_objects:
        return None
    if len(related_objects) > 1:
        raise ValueError(f"More than a single related object has been found associated with accession {accession}")
    return related_objects[0]


def call_esummary(accession, db='gds'):
    esummary_response = requests.get(f'{EUTILS_BASE_URL}/esummary.fcgi',
                                     params={'db': db,
                                             'retmode': 'json',
                                             'id': accession})
    esummary_response.raise_for_status()
    esummary_response_json = esummary_response.json()
    return esummary_response_json


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
