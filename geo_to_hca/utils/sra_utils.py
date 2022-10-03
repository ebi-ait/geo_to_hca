# --- core imports
import logging
import re
import xml.etree.ElementTree as xm

import pandas as pd

# ---application imports

# --- third-party imports
from geo_to_hca.utils.entrez_client import call_esearch, call_esummary, get_entrez_esearch, call_efetch
from geo_to_hca.utils.handle_errors import no_related_study_err

"""
Define constants.
"""

"""
Functions to handle requests from NCBI SRA database or NCBI eutils.
"""

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

            # NOTE: this is a bit too complex, requires some cleanup
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


def find_related_samples(accession):
    esummary_response_json = call_esummary(accession)
    results = [x for x in esummary_response_json['result'].values() if type(x) is dict]
    return results[0]['samples']


def find_related_object(accession, accession_type):
    esummary_response_json = call_esummary(accession, db='gds')
    results = [x for x in esummary_response_json['result'].values() if type(x) is dict]
    extrelations = [x for x in [x.get('extrelations') for x in results] for x in x]

    related_objects = [relation['targetobject'] for relation in extrelations if accession_type in relation.get('targetobject', '')]
    if not related_objects:
        return None
    if len(related_objects) > 1:
        raise ValueError(f"More than a single related object has been found associated with accession {accession}")
    return related_objects[0]


def get_srp_metadata(srp_accession: str) -> pd.DataFrame:
    """
    Function to retrieve a dataframe with multiple lists of experimental and sample accessions
    associated with a particular SRA study accession from the SRA database.
    """
    esearch_result = get_entrez_esearch(srp_accession)
    efetch_request = call_efetch(db="sra",
                                 query_key=esearch_result['querykey'],
                                 webenv=esearch_result['webenv'],
                                 rettype="runinfo",
                                 retmode="text",
                                 mode='prepare')
    log.debug(f'srp_metadata url: {efetch_request.url}')
    srp_metadata = pd.read_csv(efetch_request.url)
    if 'Run' not in srp_metadata.columns:
        raise RuntimeError(f'cannot build the srp_metadata from {efetch_request.url}: '
                           f'invalid response from efetch form {srp_accession}: missing Run column\n content: {srp_metadata}')
    return srp_metadata


def parse_xml_SRA_runs(xml_content: object) -> object:
    for experiment_package in xml_content.findall('EXPERIMENT_PACKAGE'):
        yield experiment_package


def request_fastq_from_SRA(srr_accessions: []) -> object:
    """
    Function to retrieve an xml file containing information associated with a list of NCBI SRA run accessions.
    In particular, the xml contains the paths to the data (if available) in fastq or other format.
    """
    esearch_result = get_entrez_esearch(",".join(srr_accessions))
    srr_metadata_url = call_efetch(db='sra',
                                   accessions=srr_accessions,
                                   webenv=esearch_result['webenv'],
                                   query_key=esearch_result['querykey'])
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
        db = f'biosample'
    elif accession_type == 'experiment':
        db = f'sra'
    else:
        raise ValueError(f'unsupported accession_type: {accession_type}')
    sra_url = call_efetch(db, accessions)
    return xm.fromstring(sra_url.content)


