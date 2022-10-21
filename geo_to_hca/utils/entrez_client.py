import logging
from time import sleep
from requests import Request
from xml.etree import ElementTree as xm

import requests
import requests as rq

from geo_to_hca import config
from geo_to_hca.utils import handle_errors
from geo_to_hca.utils.handle_errors import TermNotFound

log = logging.getLogger(__name__)


def throttle():
    """
    basic implementation to test whether
    throttling is the solution for the 429
    see dcp-838
    """
    # eutils allows 3 calls per second, otherwise they return 429
    sleep(0.6)


def call_esearch(geo_accession, db='gds'):
    throttle()
    r = requests.get(f'{config.EUTILS_BASE_URL}/esearch.fcgi',
                     params={
                         'db': db,
                         'retmode': 'json',
                         'term': geo_accession})
    r.raise_for_status()
    response_json = r.json()
    return response_json['esearchresult']


def call_esummary(accession, db='gds'):
    throttle()
    esummary_response = requests.get(f'{config.EUTILS_BASE_URL}/esummary.fcgi',
                                     params={'db': db,
                                             'retmode': 'json',
                                             'id': accession})
    esummary_response.raise_for_status()
    esummary_response_json = esummary_response.json()
    return esummary_response_json


def get_entrez_esearch(term, db="sra"):
    throttle()
    esearch_response = requests.get(url=f'{config.EUTILS_BASE_URL}/esearch.fcgi',
                     params={
                         "db": db,
                         "term": term,
                         "usehistory": "y",
                         "format": "json",
                     })
    log.debug(f'esearch url:  {esearch_response.url}')
    log.debug(f'esearch response status:  {esearch_response.status_code}')
    log.debug(f'esearch response content:  {esearch_response.text}')
    esearch_response.raise_for_status()
    esearch_response_json = esearch_response.json()
    esearch_result = esearch_response_json['esearchresult']
    check_esearch_result(db, term, esearch_result)
    return esearch_result


def check_esearch_result(db, term, esearch_result):
    if 'errorlist' not in esearch_result:
        return
    for error_key, errors in esearch_result['errorlist'].items():
        if len(errors) > 0:
            raise TermNotFound(term, error_key, db)
    # validation passed


def call_efetch(db, accessions=[],
                webenv=None,
                query_key=None,
                rettype=None,
                retmode=None,
                mode='call'):
    url = f'{config.EUTILS_BASE_URL}/efetch/fcgi'
    params= {
        'db': db,
    }
    if accessions:
        params['id'] = ",".join(accessions)
    if webenv:
        params['WebEnv'] = webenv
    if query_key:
        params['query_key'] = query_key
    if rettype:
        params['rettype'] = rettype
    if retmode:
        params['retmode'] = retmode
    if mode == 'call':
        efetch_response = rq.get(url, params=params)
        if efetch_response.status_code == STATUS_ERROR_CODE:
            raise handle_errors.NotFoundSRA(efetch_response, accessions)
        return efetch_response
    elif mode == 'prepare':
        return Request(method='GET',
                       url=f'{config.EUTILS_BASE_URL}/efetch.fcgi',
                       params=params).prepare()
    else:
        raise ValueError(f'unsupported call mode for efetch: {mode}')


def request_bioproject_metadata(bioproject_accession: str):
    """
    Function to request metadata at the project level given an SRA Bioproject accession.
    """
    throttle()
    srp_bioproject_url = rq.get(
        f'{config.EUTILS_BASE_URL}/efetch/fcgi?db=bioproject&id={bioproject_accession}')
    if srp_bioproject_url.status_code == STATUS_ERROR_CODE:
        raise handle_errors.NotFoundSRA(srp_bioproject_url, bioproject_accession)
    return xm.fromstring(srp_bioproject_url.content)


def request_pubmed_metadata(project_pubmed_id: str):
    """
    Function to request metadata at the publication level given a pubmed ID.
    """
    throttle()
    pubmed_url = rq.get(
        f'{config.EUTILS_BASE_URL}/efetch/fcgi?db=pubmed&id={project_pubmed_id}&rettype=xml')
    if pubmed_url.status_code == STATUS_ERROR_CODE:
        raise handle_errors.NotFoundSRA(pubmed_url, project_pubmed_id)
    return xm.fromstring(pubmed_url.content)


STATUS_ERROR_CODE = 400
