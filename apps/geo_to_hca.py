from pysradb.sraweb import SRAweb
from time import sleep
import requests as rq
import pandas as pd
import xml.etree.ElementTree as xm
import xml.dom.minidom
import openpyxl
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.utils.cell import get_column_letter
from openpyxl import load_workbook
import os,sys
import wget
import glob
import re
import math
import argparse

OPTIONAL_TABS = ['Imaged specimen', 'Organoid', 'Cell line', 'Image file', 'Additional reagents',
                 'Familial relationship']

LINKINGS = {
            'Imaged specimen': ['Imaging preparation protocol'],
            'Organoid': ['Aggregate generation protocol', 'Differentiation protocol'],
            'Cell line': ['Dissociation protocol', 'Enrichment protocol', 'Ipsc induction protocol'],
            'Image file': ['Imaging protocol', 'Imaging protocol - Channel', 'Imaging protocol - Probe']
            }

# TODO: Integrate tool with the Schema-Template-Generator's ability to generate templates from YAML instead of having
# TODO: the full template in the repo


class NotFoundSRA(Exception):
    """
    Sub-class for Exception to handle 400 error status codes.
    """
    def __init__(self, response, accession_list):
        self.response = response
        self.accessions = accession_list
        self.error = self.parse_xml_error()

    def parse_xml_error(self):
        root = xm.fromstring(self.response.content)
        return root.find('ERROR').text  # Return the string for the error returned by Efetch

    def __str__(self):
        if len(self.accessions) > 1:
            accession_string = '\n'.join(self.accessions)
        else:
            accession_string = self.accessions
        return (f"\nStatus code of the request: {self.response.status_code}.\n"
                f"Error as returned by SRA:\n{self.error}"
                f"The provided accessions were:\n{accession_string}\n\n")

class NotFoundENA(Exception):
    """
    Sub-class for Exception to handle 400 error status codes.
    """
    def __init__(self, response, title):
        self.response = response
        self.title = title
        self.error = self.parse_xml_error()

    def parse_xml_error(self):
        root = xm.fromstring(self.response.content)
        return root.find('ERROR').text  # Return the string for the error returned by Efetch

    def __str__(self):
        return (f"\nStatus code of the request: {self.response.status_code}.\n"
                f"Error as returned by SRA:\n{self.error}"
                f"The provided project title or name was:\n{self.title}\n\n")

class SraUtils:

    @staticmethod
    def sra_accession_from_geo(geo_accession: str):
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
    def srp_metadata(srp_accession: str) -> pd.DataFrame:
        sleep(0.5)
        srp_metadata_url = f'http://trace.ncbi.nlm.nih.gov/Traces/sra/sra.cgi?save=efetch&db=sra&rettype=runinfo&term={srp_accession}'
        return pd.read_csv(srp_metadata_url)

    @staticmethod
    def srr_fastq(srr_accessions):
        sleep(0.5)
        url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch/fcgi?db=sra&id={",".join(srr_accessions)}'
        srr_metadata_url = rq.get(url)
        if srr_metadata_url.status_code == 400:
            raise NotFoundSRA(srr_metadata_url, srr_accessions)
        try:
            xml = xm.fromstring(srr_metadata_url.content)
            xml_content = srr_metadata_url.content
        except:
            xml = None
            xml_content = None
        return xml,xml_content,url

    @staticmethod
    def srr_experiment(srr_accession):
        sleep(0.5)
        srr_experiment_url = rq.get(f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch/fcgi?db=sra&id={srr_accession}')
        if srr_experiment_url.status_code == 400:
            raise NotFoundSRA(srr_experiment_url, srr_accession)
        return xm.fromstring(srr_experiment_url.content)

    @staticmethod
    def srr_biosample(biosample_accession):
        sleep(0.5)
        srr_biosample_url = rq.get(f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch/fcgi?db=biosample&id={biosample_accession}')
        if srr_biosample_url.status_code == 400:
            raise NotFoundSRA(srr_biosample_url, biosample_accession)
        return xm.fromstring(srr_biosample_url.content)

    @staticmethod
    def srp_bioproject(bioproject_accession):
        sleep(0.5)
        srp_bioproject_url = rq.get(f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch/fcgi?db=bioproject&id={bioproject_accession}')
        if srp_bioproject_url.status_code == 400:
            raise NotFoundSRA(srp_bioproject_url, bioproject_accession)
        return xm.fromstring(srp_bioproject_url.content)

    @staticmethod
    def pubmed_id(project_pubmed_id):
        sleep(0.5)
        pubmed_url = rq.get(f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch/fcgi?db=pubmed&id={project_pubmed_id}&rettype=xml')
        if pubmed_url.status_code == 400:
            raise NotFoundSRA(pubmed_url, project_pubmed_id)
        return xm.fromstring(pubmed_url.content)


def fetch_srp_accession(geo_accession: str):
    srp = SraUtils.sra_accession_from_geo(geo_accession)
    if srp is not None:
        if srp.shape[0] == 1:
            srp = srp.iloc[0]["study_accession"]
        elif srp.shape[0] > 1:
            answer = input("More than 1 SRA Study Accession has been found. Is this the intended SRA study id? %s [y/n]: " % (srp.iloc[0]["study_accession"]))
            if answer.lower() in ['y', "yes"]:
                srp = srp.iloc[0]["study_accession"]
            if answer.lower() in ['n', "no"]:
                answer = input("Alternatively, is this the intended SRA study id? %s [y/n]: " % (srp.iloc[1]["study_accession"]))
                if answer.lower() in ['y', "yes"]:
                        srp = srp.iloc[1]["study_accession"]
                if answer.lower() in ['n', "no"]:
                        answer = input("Alternatively, is this the intended SRA study id? %s [y/n]: " % (srp.iloc[2]["study_accession"]))
                        if answer.lower() in ['y', "yes"]:
                            srp = srp.iloc[2]["study_accession"]
                        if answer.lower() in ['n', "no"]:
                            print("SRA study accession not found")
                            srp = None
    elif srp is None:
        answer = input("Could not recognise GEO accession %s; is it a GEO Superseries? If yes, please enter the project GEO accession manually here (GSExxxxxx) or type exit for program exit: " % (geo_accession))
        srp = SraUtils.sra_accession_from_geo(answer.upper())
        if srp is None:
            print("GEO accession still not recognised; exiting program")
        elif srp is not None:
            if srp.shape[0] == 1:
                srp = srp.iloc[0]["study_accession"]
            elif srp.shape[0] > 1:
                answer = input("More than 1 SRA Study Accession has been found. Is this the intended SRA study id? %s [y/n]: " % (srp.iloc[0]["study_accession"]))
                if answer.lower() in ['y', "yes"]:
                    srp = srp.iloc[0]["study_accession"]
                if answer.lower() in ['n', "no"]:
                    answer = input("Alternatively, is this the intended SRA study id? %s [y/n]: " % (srp.iloc[1]["study_accession"]))
                    if answer.lower() in ['y', "yes"]:
                        srp = srp.iloc[1]["study_accession"]
                    if answer.lower() in ['n', "no"]:
                        answer = input("Alternatively, is this the intended SRA study id? %s [y/n]: " % (srp.iloc[2]["study_accession"]))
                        if answer.lower() in ['y', "yes"]:
                            srp = srp.iloc[2]["study_accession"]
                        if answer.lower() in ['n', "no"]:
                            print("SRA study accession not found")
                            srp = None
    return srp

def fetch_srp_metadata(srp_accession: str) -> pd.DataFrame:
    srp_metadata_df = SraUtils.srp_metadata(srp_accession)
    return srp_metadata_df

def alternative_fastq_ENA(srp_metadata, fastq_map):
    run_accessions = list(srp_metadata['Run'])

    for accession in run_accessions:
        request_url= f'http://www.ebi.ac.uk/ena/data/warehouse/filereport?accession={accession}&result=read_run&fields=run_accession,fastq_ftp,fastq_md5,fastq_bytes'
        fastq_results = pd.read_csv(request_url, delimiter='\t')
        fastq_map[accession] = {}
        fastq_files = list(fastq_results['fastq_ftp'])[0].split(';')
        for i in range(len(fastq_files)):
            fastq_map[accession][f'read{i + 1}PairFiles'] = fastq_files[i].split('/')[-1]
    return fastq_map


def fetch_fastq_names(srr_accessions,srp_metadata):
    xml_content,content,url = SraUtils.srr_fastq(srr_accessions)
    if xml_content is None or content is None:
        print("Error parsing xml for run accessions (xml.etree.ElementTree.ParseError); cannot get fastq file names from SRA due to error in xml")
        print("Printing url for manual debugging: %s" % (url))
        fastq_map = {}
    else:
        fastq_map = {}
        available = 'yes'
        for experiment_package in parse_xml(xml_content):
            fastq_map = retrieve_fastq_from_experiment(fastq_map, experiment_package)
    if not fastq_map:
        print("fastq not found in SRA: attempting to find and get fastq from ENA. This can take some time if there are many runs.")
        fastq_map = alternative_fastq_ENA(srp_metadata, fastq_map)
        if not fastq_map:
            available = None
    return fastq_map, available

def get_dummy_fastq_map(fastq_map,srr_accessions):
    for accession in srr_accessions:
        fastq_map[accession] = {"read1PairFiles":'',"read2PairFiles":'',"read3PairFiles":''}
    return fastq_map

def fetch_biosample(biosample_accession: str):
    xml_content = SraUtils.srr_biosample(biosample_accession)
    attribute_list = list()
    biosample = xml_content.find('BioSample')
    for description in biosample.findall('Description'):
        sample_title = description.find('Title').text
    for attribute_set in biosample.findall('Attributes'):
        for attribute in attribute_set:
            attribute_list.append(attribute.text)
    return sample_title,attribute_list


def fetch_library_protocol(srr_accession: str):
    xml_content = SraUtils.srr_experiment(srr_accession)
    for experiment_package in parse_xml(xml_content):
        for experiment in experiment_package.find('EXPERIMENT'):
            library_descriptors = experiment.find('LIBRARY_DESCRIPTOR')
            if library_descriptors:
                if library_descriptors.find('LIBRARY_CONSTRUCTION_PROTOCOL'):
                    library_construction_protocol = library_descriptors.find('LIBRARY_CONSTRUCTION_PROTOCOL').text
                else:
                    library_construction_protocol = ""
    return library_construction_protocol


def fetch_sequencing_protocol(srr_accession: str):
    library_construction_protocol = fetch_library_protocol(srr_accession)
    xml_content = SraUtils.srr_experiment(srr_accession)
    for experiment_package in parse_xml(xml_content):
        for experiment in experiment_package.find('EXPERIMENT'):
            illumina = experiment.find('ILLUMINA')
            if illumina:
                instrument = illumina.find('INSTRUMENT_MODEL').text
    return library_construction_protocol,instrument


def fetch_bioproject(bioproject_accession: str):
    xml_content = SraUtils.srp_bioproject(bioproject_accession)
    bioproject_metadata = xml_content.find('DocumentSummary')
    try:
        project_name = bioproject_metadata.find("Project").find('ProjectDescr').find('Name').text
    except:
        print("no project name")
        project_name = None
    try:
        project_title = bioproject_metadata.find("Project").find('ProjectDescr').find('Title').text
    except:
        print("no project title")
        project_title = None
    try:
        project_description = bioproject_metadata.find("Project").find('ProjectDescr').find('Description').text
    except:
        project_description = ''
        print("no project description")
    project_publication = bioproject_metadata.find("Project").find('ProjectDescr').find('Publication')
    try:
        if project_publication.find('DbType').text == 'Pubmed' or project_publication.find('DbType').text == 'ePubmed':
            project_pubmed_id = project_publication.find('Reference').text
    except:
        print("No publication for project %s was found: searching project title in EuropePMC" % (bioproject_accession))
    if not project_publication or not project_pubmed_id:
        if project_title:
            print("project title is: %s" % (project_title))
            url = rq.get(f'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={project_title}')
            if url.status_code == 400:
                raise NotFoundENA(url, project_title)
            else:
                xml_content = xm.fromstring(url.content)
                try:
                    results = list()
                    result_list = xml_content.find("resultList")
                    for result in result_list:
                        results.append(result)
                    journal_title = results[0].find("journalTitle").text
                    if journal_title is None or journal_title == '':
                        project_pubmed_id = ''
                        print("no publication results for project title in ENA")
                    else:
                        answer = input("A publication title has been found: %s.\nIs this the publication title associated with the GEO accession? [y/n]: " % (journal_title))
                        if answer.lower() in ['y',"yes"]:
                            project_pubmed_id = results[0].find("pmid").text
                        else:
                            journal_title = results[1].find("journalTitle").text
                            if journal_title is None or journal_title == '':
                                project_pubmed_id = ''
                                print("no publication results for project title in ENA")
                            else:
                                answer = input("An alternative publication title has been found: %s.\nIs this the publication title associated with the GEO accession? [y/n]: " % (journal_title))
                                if answer.lower() in ['y', "yes"]:
                                    project_pubmed_id = results[1].find("pmid").text
                                else:
                                    journal_title = results[2].find("journalTitle").text
                                    if journal_title is None or journal_title == '':
                                        project_pubmed_id = ''
                                        print("no publication results for project title in ENA")
                                    else:
                                        answer = input("An alternative publication title has been found: %s.\nIs this the publication title associated with the GEO accession? [y/n]: " % (journal_title))
                                        if answer.lower() in ['y', "yes"]:
                                            project_pubmed_id = results[2].find("pmid").text
                                        else:
                                            project_pubmed_id = ''
                                            print("no publication results for project title in ENA")
                except:
                    print("no publication results for project title in ENA")
                    project_pubmed_id = ''
        if not project_pubmed_id or project_pubmed_id == '':
            if project_name:
                print("project name is %s:" % (project_name))
                url = rq.get(f'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={project_name}')
                if url.status_code == 400:
                    raise NotFoundENA(url, project_name)
                else:
                    xml_content = xm.fromstring(url.content)
                    try:
                        results = list()
                        result_list = xml_content.find("resultList")
                        for result in result_list:
                            results.append(result)
                        journal_title = results[0].find("journalTitle").text
                        if journal_title is None or journal_title == '':
                            project_pubmed_id = ''
                            print("no publication results for project name in ENA")
                        else:
                            answer = input("A publication title has been found: %s.\nIs this the publication title associated with the GEO accession? [y/n]: " % (journal_title))
                            if answer.lower() in ['y',"yes"]:
                                project_pubmed_id = results[0].find("pmid").text
                            else:
                                journal_title = results[1].find("journalTitle").text
                                if journal_title is None or journal_title == '':
                                    project_pubmed_id = ''
                                    print("no publication results for project name in ENA")
                                else:
                                    answer = input("An alternative publication title has been found: %s.\nIs this the publication title associated with the GEO accession? [y/n]: " % (journal_title))
                                    if answer.lower() in ['y', "yes"]:
                                        project_pubmed_id = results[1].find("pmid").text
                                    else:
                                        journal_title = results[2].find("journalTitle").text
                                        if journal_title is None or journal_title == '':
                                            project_pubmed_id = ''
                                            print("no publication results for project name in ENA")
                                        else:
                                            answer = input("An alternative publication title has been found: %s.\nIs this the publication title associated with the GEO accession? [y/n]: " % (journal_title))
                                            if answer.lower() in ['y', "yes"]:
                                                project_pubmed_id = results[2].find("pmid").text
                                            else:
                                                project_pubmed_id = ''
                                                print("no publication results for project name in ENA")
                    except:
                        print("no publication results for project name in ENA")
                        project_pubmed_id = ''
        if not project_pubmed_id or project_pubmed_id == '':
            project_title = ''
            project_name = ''
            project_pubmed_id = ''
    return project_name,project_title,project_description,project_pubmed_id

def fetch_pubmed(project_pubmed_id: str,iteration: int):
    xml_content = SraUtils.pubmed_id(project_pubmed_id)
    author_list = list()
    grant_list=  list()
    try:
        title = xml_content.find("PubmedArticle").find("MedlineCitation").find("Article").find("ArticleTitle").text
    except:
        title = ''
        if iteration == 1:
            print("no publication title found")
    try:
        authors = xml_content.find("PubmedArticle").find("MedlineCitation").find("Article").find("AuthorList")
    except:
        if iteration == 1:
            print("no authors found in SRA")
        try:
            url = rq.get(f'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={title}')
            if url.status_code == 400:
                raise NotFoundENA(url, title)
            else:
                xml_content_2 = xm.fromstring(url.content)
            try:
                results = list()
                result_list = xml_content_2.find("resultList")
                for result in result_list:
                    results.append(result)
                author_string = results[0].find("authorString").text
                print(author_string)
                #doi = results[0].find("doi").text
            except:
                authors = None
                if iteration == 1:
                    print("no authors found in ENA")
        except:
            authors = None
            if iteration == 1:
                print("no authors found in ENA")
    if authors is not None:
        for author in authors:
            try:
                lastname = author.find("LastName").text
            except:
                lastname = ''
            try:
                forename = author.find("ForeName").text
            except:
                forename = ''
            try:
                initials = author.find("Initials").text
            except:
                initials = ''
            try:
                affiliation = author.find('AffiliationInfo').find("Affiliation").text
            except:
                affiliation = ''
            author_list.append([lastname,forename,initials,affiliation])
    try:
        grants = xml_content.find("PubmedArticle").find("MedlineCitation").find("Article").find("GrantList")
    except:
        grants = None
        if iteration == 1:
            print("no grants found in SRA or ENA")
    if grants is not None:
        for grant in grants:
            try:
                id = grant.find("GrantID").text
            except:
                id = ''
            try:
                agency = grant.find("Agency").text
            except:
                agency = ''
            grant_list.append([id,agency])
    try:
        articles = xml_content.find('PubmedArticle').find('PubmedData').find('ArticleIdList')
        for article_id in articles:
            if "/" in article_id.text:
                article_doi_id = article_id.text
    except:
        article_doi_id = ''
        if iteration == 1:
            print("no publication doi found")
    return title,author_list,grant_list,article_doi_id


def parse_xml(xml_content):
    for experiment_package in xml_content.findall('EXPERIMENT_PACKAGE'):
        yield experiment_package


def extract_read_information(general_read_values):
    reads = {}
    if "--read1PairFiles" not in general_read_values or "--read2PairFiles" not in general_read_values or "--read3PairFiles" not in general_read_values:
        return None
    else:
        read_info_list = general_read_values.strip().split('--')[1:]
        for read_info in read_info_list:
            read_info = read_info.strip()
            split_read = read_info.split("=")
            reads[split_read[0]] = split_read[1]
    return reads

def new_extract_read_information(sra_file_list, fastq_map):
    i = 1
    for read_info in sra_file_list:
        for alternative in list(read_info):
            if 'url' in alternative.attrib:
                if "fastq" in alternative.attrib['url']:
                    #Asumes there is an order R1, R2, I1, I2
                    filename = alternative.attrib['url'].split('/')[-1]
                    accession = alternative.attrib['url'].split('/')[-2]
                    if accession not in fastq_map.keys():
                        fastq_map[accession] = {}
                    fastq_map[accession][f'read{i}PairFiles'] = filename
                    i += 1
                    break
                elif "fastq" not in alternative.attrib['url']:
                    filename = ''
                    accession = alternative.attrib['url'].split('/')[-2]
                    if accession not in fastq_map.keys():
                        fastq_map[accession] = {}
                    fastq_map[accession][f'read{i}PairFiles'] = filename
                    i += 1
                    break
    return fastq_map

def retrieve_fastq_from_experiment(fastq_map,experiment_package):
    def get_reads(fastq_map,experiment_package):
        for run_set in experiment_package.findall('RUN_SET'):
            for run in run_set.findall('RUN'):
                run_attributes = run.findall('SRAFiles')
                for sra_files in run_attributes:
                    run_reads = []
                    for sra_file in sra_files.findall('SRAFile'):
                        attributes = sra_file.attrib
                        # Check files are public and not in SRA format
                        if attributes['cluster'] == 'public':
                            if attributes['sratoolkit']:
                                if attributes['sratoolkit'] != '1':
                                    run_reads.append(sra_file)
                            else:
                                run_reads.append(sra_file)
                    if run_reads:
                        fastq_map = new_extract_read_information(run_reads, fastq_map)
                    else:
                        return {}
                    """
                    for attributes in sra_file.findall('RUN_ATTRIBUTE'):  # More than one attribute and they all have the same tag
                        if attributes.find('TAG').text == 'options':
                            reads = extract_read_information(attributes.find('VALUE').text)
                            if reads:
                                fastq_map[run.attrib['accession']] = reads
                            else:
                                return {}
                    """
        return fastq_map
    fastq_map = get_reads(fastq_map,experiment_package)
    return fastq_map


#def initialise(srp_metadata):
#    count = 1
#    cell_suspension = list(srp_metadata['Experiment'])[0]
#    run = list(srp_metadata['Run'])[0]
#    lane_index = 1
#    return count,cell_suspension,run,lane_index


#def get_process_id(row,process_id,cell_suspension):
#    count = int(process_id.split("process_")[1])
#    if row['Experiment'] == cell_suspension:
#        process_id = process_id
#    else:
#        count += 1
#        process_id = 'process_' + str(count)
#    return process_id


#def get_lane_index(row,cell_suspension,run,lane_index):
#    if row['Experiment'] == cell_suspension and row['Run'] == run:
#        lane_index = lane_index
#    elif row['Experiment'] == cell_suspension and row['Run'] != run:
#        lane_index += 1
#    elif row['Experiment'] != cell_suspension:
#        lane_index = 1
#    return lane_index


# TODO Changed this to not depend on fastq map name conventions
# TODO add print statement to this function when no R1, R2, R3, R4
def get_row(row, file_index, process_id, lane_index, fastq_map):
    new_row = row
    if not fastq_map:
        new_row['fastq_name'] = ''
        new_row['fastq_file'] = ''
    else:
        try:
            if fastq_map[row['Run']]:
                new_row['fastq_name'] = fastq_map[row['Run']].get(file_index)
            else:
                new_row['fastq_name'] = ''
            if "I1" in new_row['fastq_name'] or "R3" in new_row['fastq_name']:
                new_row['fastq_file'] = 'index1'
            elif "R1" in new_row['fastq_name']:
                new_row['fastq_file'] = 'read1'
            elif "R2" in new_row['fastq_name']:
                new_row['fastq_file'] = 'read2'
            elif "R4" in new_row['fastq_name'] or "I2" in new_row['fastq_name']:
                new_row['fastq_file'] = 'index2'
            else:
                new_row['fastq_file'] = ''
        except:
                new_row['fastq_name'] = ''
                new_row['fastq_file'] = ''
    new_row['process_id'] = process_id
    new_row['lane_index'] = lane_index
    return new_row

# TODO add changelog for this function. Accounted lanes
def integrate_metadata(srp_metadata,fastq_map):
    SRP_df = pd.DataFrame()
    #count,cell_suspension,run,lane_index = initialise(srp_metadata)
    for index, row in srp_metadata.iterrows():
        #process_id = get_process_id(row,process_id,cell_suspension)
        srr_accession = row['Run']
        if len(fastq_map[srr_accession]) >= 3:
            result = "yes"
            for i in range(len(fastq_map[srr_accession])):
                if re.search('_L[0-9]{3}', "".join(fastq_map[srr_accession].values())):
                    filename = fastq_map[srr_accession][f'read{i + 1}PairFiles']
                    try:
                        lane_index = int(re.findall('L[0-9]{3}', filename)[0][-1])
                    except:
                        try:
                            lane_index = int(re.findall('L[0-9]{4}', filename)[0][-1])
                        except:
                            lane_index = ''
                else:
                    lane_index = ''
                process_id = ''
                new_row = get_row(row, f'read{(i + 1)}PairFiles', process_id, lane_index, fastq_map)
                SRP_df = SRP_df.append(new_row, ignore_index=True)
        if len(fastq_map[srr_accession]) < 3:
            print("No fastq file name for Run accession: %s" % (srr_accession))
            result = "no"
            for i in range(0,3):
                lane_index = ''
                process_id=''
                new_row = get_row(row,f'read{(i + 1)}PairFiles',process_id,lane_index,fastq_map)
                SRP_df = SRP_df.append(new_row, ignore_index=True)
    return SRP_df,result


def get_empty_df(workbook,tab_name):
    sheet = workbook[tab_name]
    values = sheet.values
    empty_df = pd.DataFrame(values)
    cols = empty_df.loc[0,]
    tab = pd.DataFrame(columns=cols)
    return tab


def write_to_wb(workbook: Workbook, tab_name: str, tab_content: pd.DataFrame) -> None:
    """
    Write the tab to the active workbook.
    :param workbook: str
                     Workbook extracted from the template
    :param tab_name: str
                     Name of the tab that is being modified
    :param tab_content: str
                        Content of the tab

    :returns None
    """
    worksheet = workbook[tab_name]
    # If more than 1 series is being filled for the same spreadsheet, find the first unfilled row
    row_not_filled = 6
    while True:
        if worksheet[f'A{row_not_filled}'].value or worksheet[f'B{row_not_filled}'].value:
            row_not_filled += 1
        else:
            break

    for index, key in enumerate(worksheet[4]):
        if not key.value:
            break
        if key.value not in tab_content.keys():
            continue
        for i in range(len(tab_content[key.value])):
            worksheet[f"{get_column_letter(index + 1)}{i + row_not_filled}"] = list(tab_content[key.value])[i]


def get_sequence_file_tab_xls(SRP_df,workbook,tab_name):
    tab = get_empty_df(workbook,tab_name)
    for index,row in SRP_df.iterrows():
        tab = tab.append({'sequence_file.file_core.file_name': row['fastq_name'],
                          'sequence_file.file_core.format': 'fastq.gz',
                          'sequence_file.file_core.content_description.text':'DNA sequence',
                          'sequence_file.read_index': row['fastq_file'],
                          'sequence_file.lane_index': row['lane_index'],
                          'sequence_file.insdc_run_accessions': row['Run'],
                          'process.insdc_experiment.insdc_experiment_accession': row['Experiment'],
                          'cell_suspension.biomaterial_core.biomaterial_id':row['Experiment'],
                          'library_preparation_protocol.protocol_core.protocol_id':'',
                          'sequencing_protocol.protocol_core.protocol_id':'',
                          'process.process_core.process_id':row['Run']}, ignore_index=True)
    tab = tab.sort_values(by='sequence_file.insdc_run_accessions')
    return tab


def get_cell_suspension_tab_xls(SRP_df,workbook,out_file,tab_name):
    tab = get_empty_df(workbook, tab_name)
    experiments_dedup = list(set(list(SRP_df['Experiment'])))
    for experiment in experiments_dedup:
        biosample = list(SRP_df.loc[SRP_df['Experiment'] == experiment]['BioSample'])[0]
        gsm_sample = list(SRP_df.loc[SRP_df['Experiment'] == experiment]['SampleName'])[0]
        tab = tab.append({'cell_suspension.biomaterial_core.biomaterial_id':experiment,
                          'cell_suspension.biomaterial_core.biomaterial_name':gsm_sample,
                         'specimen_from_organism.biomaterial_core.biomaterial_id':biosample,
                          'cell_suspension.biomaterial_core.ncbi_taxon_id':list(SRP_df.loc[SRP_df['Experiment'] == experiment]['TaxID'])[0],
                         'cell_suspension.genus_species.text':list(SRP_df.loc[SRP_df['Experiment'] == experiment]['ScientificName'])[0],
                         'cell_suspension.biomaterial_core.biosamples_accession':biosample}, ignore_index=True)
    tab = tab.sort_values(by='cell_suspension.biomaterial_core.biomaterial_id')
    write_to_wb(workbook, tab_name, tab)


def get_specimen_from_organism_tab_xls(SRP_df,workbook,out_file,tab_name):
    tab = get_empty_df(workbook, tab_name)
    samples_dedup = list(set(list(SRP_df['BioSample'])))
    for biosample_accession in samples_dedup:
        sample_title,attribute_list = fetch_biosample(biosample_accession)
        tab = tab.append({'specimen_from_organism.biomaterial_core.biomaterial_id':biosample_accession,
                          'specimen_from_organism.biomaterial_core.biomaterial_name':sample_title,
                          'specimen_from_organism.biomaterial_core.biomaterial_description': ','.join(attribute_list),
                          'specimen_from_organism.biomaterial_core.ncbi_taxon_id': list(SRP_df.loc[SRP_df['BioSample'] == biosample_accession]['TaxID'])[0],
                          'specimen_from_organism.genus_species.text': list(SRP_df.loc[SRP_df['BioSample'] == biosample_accession]['ScientificName'])[0],
                          'specimen_from_organism.genus_species.ontology_label': list(SRP_df.loc[SRP_df['BioSample'] == biosample_accession]['ScientificName'])[0],
                          'specimen_from_organism.biomaterial_core.biosamples_accession': biosample_accession,
                          'specimen_from_organism.biomaterial_core.insdc_sample_accession': list(SRP_df.loc[SRP_df['BioSample'] == biosample_accession]['Sample'])[0],
                          'collection_protocol.protocol_core.protocol_id':'',
                          'process.insdc_experiment.insdc_experiment_accession':SRP_df[SRP_df['BioSample'] == biosample_accession]['Experiment'].values.tolist()[0]}, ignore_index=True)
    tab = tab.sort_values(by='process.insdc_experiment.insdc_experiment_accession')
    write_to_wb(workbook, tab_name, tab)


def get_library_protocol_tab_xls(SRP_df,workbook,out_file,tab_name):
    tab = get_empty_df(workbook, tab_name)
    experiments_dedup = list(set(list(SRP_df['Experiment'])))
    count = 0
    library_protocol_set = list()
    library_protocol_dict = {}
    for experiment in experiments_dedup:
        library_protocol = fetch_library_protocol(experiment)
        if library_protocol not in library_protocol_set:
            count += 1
            library_protocol_id = "library_protocol_" + str(count)
            library_protocol_set.append(library_protocol)
            tmp_dict = {'library_preparation_protocol.protocol_core.protocol_id':library_protocol_id,
                              'library_preparation_protocol.protocol_core.protocol_description': library_protocol,
                              'library_preparation_protocol.input_nucleic_acid_molecule.text': 'polyA RNA',
                              'library_preparation_protocol.nucleic_acid_source':'single cell'}
            library_protocol_dict[experiment] = {"library_protocol_id":library_protocol_id,"library_protocol_description":
                library_protocol}
            if "10X" in library_protocol:
                if "v.2" or "v2" in library_protocol:
                    tmp_dict.update({'library_preparation_protocol.cell_barcode.barcode_read': 'Read1',
                                     'library_preparation_protocol.cell_barcode.barcode_offset': 0,
                                     'library_preparation_protocol.cell_barcode.barcode_length': 16,
                                     'library_preparation_protocol.library_construction_method.text':"10X 3' v2 sequencing",
                                     'library_preparation_protocol.library_construction_kit.retail_name': 'Single Cell 3’ Reagent Kit v2',
                                     'library_preparation_protocol.library_construction_kit.manufacturer': '10X Genomics',
                                     'library_preparation_protocol.end_bias':'3 prime tag',
                                     'library_preparation_protocol.primer':'poly-dT',
                                     'library_preparation_protocol.strand':'first',
                                     'library_preparation_protocol.umi_barcode.barcode_read':'Read1',
                                     'library_preparation_protocol.umi_barcode.barcode_offset':16,
                                     'library_preparation_protocol.umi_barcode.barcode_length':10})
                elif "v.3" or "v3" in library_protocol:
                    tmp_dict.update({'library_preparation_protocol.cell_barcode.barcode_read': '',
                                    'library_preparation_protocol.cell_barcode.barcode_offset': '',
                                    'library_preparation_protocol.cell_barcode.barcode_length': '',
                                    'library_preparation_protocol.library_construction_method.text':"10X 3' v3 sequencing",
                                    'library_preparation_protocol.library_construction_kit.retail_name': 'Single Cell 3’ Reagent Kit v3',
                                    'library_preparation_protocol.library_construction_kit.manufacturer': '10X Genomics',
                                    'library_preparation_protocol.end_bias':'',
                                    'library_preparation_protocol.primer':'',
                                    'library_preparation_protocol.strand':'',
                                    'library_preparation_protocol.umi_barcode.barcode_read':'',
                                    'library_preparation_protocol.umi_barcode.barcode_offset':'',
                                    'library_preparation_protocol.umi_barcode.barcode_length':''})
                else:
                    tmp_dict.update({'library_preparation_protocol.library_construction_method.text': "10X sequencing",
                                     'library_preparation_protocol.library_construction_kit.manufacturer': '10X Genomics'})
            tab = tab.append(tmp_dict,ignore_index=True)
        else:
            tab = tab
        if library_protocol in library_protocol_set:
            tab = tab
            for key in library_protocol_dict.keys():
                if library_protocol_dict[key]["library_protocol_description"] == library_protocol:
                    library_protocol_id = library_protocol_dict[key]["library_protocol_id"]
            if not library_protocol_id:
                library_protocol_id = ''
            else:
                library_protocol_dict[experiment] = {"library_protocol_id":library_protocol_id,"library_protocol_description":
                library_protocol}
    write_to_wb(workbook, tab_name, tab)
    return library_protocol_dict


def get_sequencing_protocol_tab_xls(SRP_df,workbook,out_file,tab_name):
    tab = get_empty_df(workbook, tab_name)
    experiments_dedup = list(set(list(SRP_df['Experiment'])))
    count = 0
    sequencing_protocol_id = "sequencing_protocol_1"
    sequencing_protocol_set = list()
    sequencing_protocol_dict = {}
    for experiment in experiments_dedup:
        library_construction_protocol,instrument = fetch_sequencing_protocol(experiment)
        if "10X" in library_construction_protocol:
            paired_end = 'no'
            method = 'tag based single cell RNA sequencing'
        elif "10X" not in library_construction_protocol:
            paired_end = ''
            method = ''
        sequencing_protocol_description = [instrument,method]
        if sequencing_protocol_description not in sequencing_protocol_set:
            count += 1
            sequencing_protocol_id = "sequencing_protocol_" + str(count)
            sequencing_protocol_set.append(sequencing_protocol_description)
            sequencing_protocol_dict[experiment] = {"sequencing_protocol_id":sequencing_protocol_id,
                                                    "sequencing_protocol_description":sequencing_protocol_description}
            tab = tab.append({'sequencing_protocol.protocol_core.protocol_id': sequencing_protocol_id,
                              'sequencing_protocol.instrument_manufacturer_model.text': instrument,
                              'sequencing_protocol.paired_end': paired_end,
                              'sequencing_protocol.method.text': method}, ignore_index=True)
        if sequencing_protocol_description in sequencing_protocol_set:
            tab = tab
            for key in sequencing_protocol_dict.keys():
                if sequencing_protocol_dict[key]["sequencing_protocol_description"] == sequencing_protocol_description:
                    sequencing_protocol_id = sequencing_protocol_dict[key]["sequencing_protocol_id"]
            if not sequencing_protocol_id:
                sequencing_protocol_id = ''
            else:
                sequencing_protocol_dict[experiment] = {"sequencing_protocol_id":sequencing_protocol_id,
                                                    "sequencing_protocol_description":sequencing_protocol_description}
    write_to_wb(workbook, tab_name, tab)
    return sequencing_protocol_dict


def update_sequence_file_tab_xls(sequence_file_tab,library_protocol_dict,sequencing_protocol_dict,workbook,out_file,tab_name):
    library_protocol_id_list = list()
    sequencing_protocol_id_list = list()
    for index,row in sequence_file_tab.iterrows():
        library_protocol_id_list.append(library_protocol_dict[row["cell_suspension.biomaterial_core.biomaterial_id"]]["library_protocol_id"])
        sequencing_protocol_id_list.append(sequencing_protocol_dict[row["cell_suspension.biomaterial_core.biomaterial_id"]]["sequencing_protocol_id"])
    sequence_file_tab['library_preparation_protocol.protocol_core.protocol_id'] = library_protocol_id_list
    sequence_file_tab['sequencing_protocol.protocol_core.protocol_id'] = sequencing_protocol_id_list
    write_to_wb(workbook, tab_name, sequence_file_tab)


# TODO Actually fix error instead of avoiding it
def get_project_main_tab_xls(SRP_df,workbook,geo_accession,out_file,tab_name):
    study = list(SRP_df['SRAStudy'])[0]
    project = list(SRP_df['BioProject'])[0]
    try:
        tab = get_empty_df(workbook,tab_name)
        bioproject = list(set(list(SRP_df['BioProject'])))
        if len(bioproject) > 1:
            print("more than 1 bioproject, check this")
        else:
            bioproject = bioproject[0]
        project_name,project_title,project_description,project_pubmed_id = fetch_bioproject(bioproject)
        tab = tab.append({'project.project_core.project_title':project_title,
                          'project.project_core.project_description':project_description,
                          'project.geo_series_accessions':geo_accession,
                          'project.insdc_study_accessions':study,
                          'project.insdc_project_accessions':project}, ignore_index=True)
        write_to_wb(workbook, tab_name, tab)
    except AttributeError:
        pass
    return project_name,project_title,project_description,project_pubmed_id


def get_project_publication_tab_xls(workbook,tab_name,project_pubmed_id):
    tab = get_empty_df(workbook,tab_name)
    title,author_list,grant_list,article_doi_id = fetch_pubmed(project_pubmed_id,iteration=1)
    name_list = list()
    for author in author_list:
        name = author[0] + ' ' + author[2] + "||"
        name_list.append(name)
    name_list = ''.join(name_list)
    name_list = name_list[:len(name_list)-2]
    tab = tab.append({'project.publications.authors':name_list,
                      'project.publications.title':title,
                      'project.publications.doi':article_doi_id,
                      'project.publications.pmid':project_pubmed_id,
                      'project.publications.url':''}, ignore_index=True)
    write_to_wb(workbook, tab_name, tab)


def get_project_contributors_tab_xls(workbook,tab_name,project_pubmed_id):
    tab = get_empty_df(workbook,tab_name)
    title, author_list, grant_list, article_doi_id = fetch_pubmed(project_pubmed_id,iteration=2)
    for author in author_list:
        name = author[1] + ',,' + list(author)[0]
        affiliation = author[3]
        tab = tab.append({'project.contributors.name':name,'project.contributors.institution':affiliation}, ignore_index=True)
    write_to_wb(workbook, tab_name, tab)


def get_project_funders_tab_xls(workbook,tab_name,project_pubmed_id):
    tab = get_empty_df(workbook,tab_name)
    title, author_list, grant_list, article_doi_id = fetch_pubmed(project_pubmed_id,iteration=3)
    for grant in grant_list:
        tab = tab.append({'project.funders.grant_id':grant[0],'project.funders.organization':grant[1]}, ignore_index=True)
    write_to_wb(workbook, tab_name, tab)


def empty_worksheet(worksheet):
    if worksheet['A6'].value or worksheet['B6'].value:
        return False
    return True

def delete_unused_worksheets(workbook: Workbook) -> None:
    """
    Delete unused sheets from the metadata spreadsheet and the linked protocols.

    :param workbook: Workbook
                     Workbook object containing the metadata spreadsheet being modified
    :returns None
    """

    for worksheet_name in OPTIONAL_TABS:
        current_worksheet = workbook[worksheet_name]
        if current_worksheet and empty_worksheet(current_worksheet):
            del workbook[worksheet_name]
            if worksheet_name in LINKINGS:
                for linked_sheet in LINKINGS[worksheet_name]:
                    if empty_worksheet(workbook[linked_sheet]):
                        del workbook[linked_sheet]


def return_gse_from_superseries(geo_accession: str) -> str:
    sys.stdout = open(os.devnull, "w")
    try:
        gds = SRAweb().fetch_gds_results(geo_accession)
        unique_gse = list(set(list(gds['gse'])))
        unique_gse = [f"GSE{gse}" for gse in unique_gse]
    except SystemExit:
        unique_gse = [geo_accession]
    sys.stdout = sys.__stdout__
    return ",".join(unique_gse)

def get_superseries_from_gse(geo_accession: str) -> str:
    sys.stdout = open(os.devnull, "w")
    superseries = geo_accession
    try:
        gds = SRAweb().fetch_gds_results(geo_accession)
        unique_gse = list(set(list(gds['gse'])))
        for gse in unique_gse:
            if ";" in gse:
                superseries = [f"GSE{gse.split(';')[1]}"]
    except SystemExit:
        pass
    sys.stdout = sys.__stdout__
    return superseries

def list_str(values):
    if "," not in values:
        raise argparse.ArgumentTypeError("Argument list not valid: comma separated list required")
    return values.split(',')

def check_file(path):
    if not os.path.exists(path):
        raise argparse.ArgumentTypeError("file %s does not exist" % (path))
    try:
        df = pd.read_csv(path, sep="\t")
    except:
        raise argparse.ArgumentTypeError("file %s is not a valid format" % (path))
    try:
        geo_accession_list = list(df["accession"])
    except:
        raise argparse.ArgumentTypeError("accession list column not found in file %s" % (path))
    return geo_accession_list

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--accession',type=str,help='GEO accession (str)')
    parser.add_argument('--accession_list',type=list_str,help='GEO accession list (comma separated)')
    parser.add_argument('--input_file',type=check_file,help='optional path to tab-delimited input .txt file')
    parser.add_argument('--template',default="docs/hca_template.xlsx",
                        help='path to an HCA spreadsheet template (xlsx)')
    parser.add_argument('--header_row',type=int,default=4,
                        help='header row with HCA programmatic names')
    parser.add_argument('--input_row1',type=int,default=6,
                        help='HCA metadata input start row')
    parser.add_argument('--output_dir',default='spreadsheets/',
                        help='path to output directory; if it does not exist, the directory will be created')
    parser.add_argument('--output_log',type=bool,default=True,
                        help='True/False: should the output result log be created')

    args = parser.parse_args()

    # check user-specified arguments are valid

    if args.input_file:
        geo_accession_list = args.input_file
    elif args.accession_list:
        geo_accession_list = args.accession_list
    elif args.accession:
        geo_accession_list = [args.accession]
    else:
        print("GEO accession input is not specified")
        sys.exit()

    if not os.path.exists(args.template):
        print("path to HCA template file not found; will revert to default: docs/hca_template.xlsx")
        template = "docs/hca_template.xlsx"
    try:
        workbook = load_workbook(filename=args.template)
        template = args.template
    except:
        print("specified HCA template file is not valid xlsx; will revert to default: docs/hca_template.xlsx")
        template = "docs/hca_template.xlsx"

    if not os.path.exists(args.output_dir):
        os.mkdir(args.output_dir)

    # initialise dictionary to summarise results
    results = {}

    # for each geo accession:
    for geo_accession in geo_accession_list:

        if ',' in geo_accession:
            geo_accession = get_superseries_from_gse(geo_accession.split(',')[0])
            geo_accession = return_gse_from_superseries(geo_accession)
        superseries = geo_accession if isinstance(geo_accession, str) else geo_accession[0]

        # create a new output file name to store the hca converted metadata
        out_file = f"{args.output_dir}/{superseries}.xlsx"

        # load an empty template HCA metadata excel spreadsheet. All tabs and fields should be in this template.
        workbook = load_workbook(filename=template)

        if isinstance(geo_accession, str):
            geo_accession = [geo_accession]

        for accession in geo_accession:
            print(f"processing GEO dataset {accession}")

            # fetch the SRA study accession given the geo accession
            srp_accession = fetch_srp_accession(accession)

            if srp_accession is None:
                results[accession] = {"SRA Study available": "no"}
                results[accession].update({"fastq files available": "na"})
                continue

            else:
                results[accession] = {"SRA Study available": "yes"}

                # if an srp study accession can be found, fetch the SRA study metadata for the srp accession
                srp_metadata = fetch_srp_metadata(srp_accession)

                # get fastq file names
                fastq_map, available = fetch_fastq_names(list(srp_metadata['Run']),srp_metadata)

                # TODO create fastq_map check method for number of fastq files
                # store whether the fastq files were available

                if not available:

                    results[accession].update({"fastq files available": "no"})
                    continue

                else:

                    # integrate metadata and fastq file names into a single dataframe
                    SRP_df,result = integrate_metadata(srp_metadata, fastq_map)
                    if result == "no":
                        results[accession].update({"All fastq files are available": "no"})
                    elif result == "yes":
                        results[accession].update({"All fastq files are available": "yes"})

                    # get HCA Sequence file metadata: fetch as many fields as is possible using the above metadata accessions
                    sequence_file_tab = get_sequence_file_tab_xls(SRP_df,workbook,tab_name="Sequence file")

                    # get HCA Cell suspension metadata: fetch as many fields as is possible using the above metadata accessions
                    get_cell_suspension_tab_xls(SRP_df,workbook,out_file,tab_name="Cell suspension")

                    # get HCA Specimen from organism metadata: fetch as many fields as is possible using the above metadata accessions
                    get_specimen_from_organism_tab_xls(SRP_df,workbook,out_file,tab_name="Specimen from organism")

                    # get HCA Library preparation protocol metadata: fetch as many fields as is possible using the above metadata accessions
                    library_protocol_dict = get_library_protocol_tab_xls(SRP_df,workbook,out_file,
                                                                        tab_name="Library preparation protocol")

                    # get HCA Sequencing protocol metadata: fetch as many fields as is possible using the above metadata accessions
                    sequencing_protocol_dict = get_sequencing_protocol_tab_xls(SRP_df,workbook,out_file,
                                                                        tab_name="Sequencing protocol")

                    # update HCA Sequence file metadata with the correct library preparation protocol ids and sequencing protocol ids
                    update_sequence_file_tab_xls(sequence_file_tab,library_protocol_dict,sequencing_protocol_dict,
                                                workbook, out_file, tab_name="Sequence file")

                    # get Project metadata: fetch as many fields as is possible using the above metadata accessions
                    project_name, project_title, project_description, project_pubmed_id = get_project_main_tab_xls(SRP_df,workbook,accession,out_file,tab_name="Project")

                    try:
                        # get Project - Publications metadata: fetch as many fields as is possible using the above metadata accessions
                        get_project_publication_tab_xls(workbook,tab_name="Project - Publications",project_pubmed_id=project_pubmed_id)
                    except AttributeError:
                        print(f'Publication attribute error with GEO project {accession}')

                    try:
                        # get Project - Contributors metadata: fetch as many fields as is possible using the above metadata accessions
                        get_project_contributors_tab_xls(workbook,tab_name="Project - Contributors",project_pubmed_id=project_pubmed_id)
                    except AttributeError:
                        print(f'Contributors attribute error with GEO project {accession}')

                    try:
                        # get Project - Funders metadata: fetch as many fields as is possible using the above metadata accessions
                        get_project_funders_tab_xls(workbook,tab_name="Project - Funders",project_pubmed_id=project_pubmed_id)
                    except AttributeError:
                        print(f'Funders attribute error with GEO project {accession}')

        # Make the spreadsheet more readable by deleting all the unused OPTIONAL_TABS and unused linked protocols
        delete_unused_worksheets(workbook)

        # Done
        workbook.save(out_file)

    results = pd.DataFrame.from_dict(results).transpose()
    print("showing result")
    print(results)
    if args.output_log:
        results.to_csv(f"{args.output_dir}/results_{superseries}.log",sep="\t")
    print("Done.")


if __name__ == "__main__":
    main()
