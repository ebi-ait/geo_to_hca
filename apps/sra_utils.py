"""
Import required modules.
"""
from pysradb.sraweb import SRAweb
from time import sleep
import requests as rq
import xml.etree.ElementTree as xm
import pandas as pd

import handle_errors
import parse_reads

"""
Define constants.
"""
STATUS_ERROR_CODE = 400

"""
Define functions.
"""
class SraUtils:
    """
    Class to handle requests from NCBI SRA database via SRAweb() or NCBI eutils.
    """
    @staticmethod
    def get_srp_accession_from_geo(geo_accession: str) -> str:
        """
        Function to retrieve an SRA database study accession for a given input GEO accession.
        """
        sleep(0.5)
        try:
            srp = SRAweb().gse_to_srp(geo_accession)
        except:
            srp = None
        if not isinstance(srp, pd.DataFrame):
            srp = None
        elif isinstance(srp, pd.DataFrame):
            if srp.shape[0] == 0:
                srp = None
            else:
                srp = srp
        return srp

    @staticmethod
    def get_srp_metadata(srp_accession: str) -> pd.DataFrame:
        """
        Function to retrieve a dataframe with multiple lists of experimental and sample accessions
        associated with a particular SRA study accession from the SRA database.
        """
        sleep(0.5)
        srp_metadata_url = f'http://trace.ncbi.nlm.nih.gov/Traces/sra/sra.cgi?save=efetch&db=sra&rettype=runinfo&term={srp_accession}'
        return pd.read_csv(srp_metadata_url)

    @staticmethod
    def request_fastq_from_ENA(srp_accession: str) -> {}:
        """
        Function to retrieve fastq file paths from ENA given an SRA study accession. The request returns a
        dataframe with a list of run accessions and their associated fastq file paths. The multiple file paths for
        each run are stored in a single string. This string is then stored in a dictionary with the associated
        run accessions as keys.
        """
        try:
            request_url = f'http://www.ebi.ac.uk/ena/data/warehouse/filereport?accession={srp_accession}&result=read_run&fields=run_accession,fastq_ftp'
            fastq_results = pd.read_csv(request_url, delimiter='\t')
            fastq_map = {list(fastq_results['run_accession'])[i]: parse_reads.extract_reads_ENA(list(fastq_results['fastq_ftp'])[i]) for i
                         in range(0, len(list(fastq_results['run_accession'])))}
            return fastq_map
        except:
            return None

    @staticmethod
    def request_fastq_from_SRA(srr_accessions: []) -> object:
        """
        Function to retrieve an xml file containing information associated with a list of NCBI SRA run accessions.
        In particular, the xml contains the paths to the data (if available) in fastq or other format.
        """
        sleep(0.5)
        url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch/fcgi?db=sra&id={",".join(srr_accessions)}'
        srr_metadata_url = rq.get(url)
        if srr_metadata_url.status_code == STATUS_ERROR_CODE:
            raise handle_errors.NotFoundSRA(srr_metadata_url, srr_accessions)
        try:
            xml_content = srr_metadata_url.content
        except:
            xml_content = None
        return xml_content

    @staticmethod
    def request_accession_info(accessions: [],accession_type: str) -> object:
        """
        Function which sends a request to NCBI SRA database to get an xml file with metadata about a
        given list of biosample or experiment accessions. The xml contains various metadata fields.
        """
        if accession_type == 'biosample':
            url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch/fcgi?db=biosample&id={",".join(accessions)}'
        if accession_type == 'experiment':
            url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch/fcgi?db=sra&id={",".join(accessions)}'
        sra_url = rq.get(url)
        if sra_url.status_code == STATUS_ERROR_CODE:
            raise handle_errors.NotFoundSRA(sra_url, accessions)
        return xm.fromstring(sra_url.content)

    @staticmethod
    def request_bioproject_metadata(bioproject_accession: str):
        """
        Function to request metadata at the project level given an SRA Bioproject accession.
        """
        sleep(0.5)
        srp_bioproject_url = rq.get(f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch/fcgi?db=bioproject&id={bioproject_accession}')
        if srp_bioproject_url.status_code == STATUS_ERROR_CODE:
            raise handle_errors.NotFoundSRA(srp_bioproject_url, bioproject_accession)
        return xm.fromstring(srp_bioproject_url.content)

    @staticmethod
    def request_pubmed_metadata(project_pubmed_id: str):
        """
        Function to request metadata at the publication level given a pubmed ID.
        """
        sleep(0.5)
        pubmed_url = rq.get(f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch/fcgi?db=pubmed&id={project_pubmed_id}&rettype=xml')
        if pubmed_url.status_code == STATUS_ERROR_CODE:
            raise handle_errors.NotFoundSRA(pubmed_url, project_pubmed_id)
        return xm.fromstring(pubmed_url.content)
