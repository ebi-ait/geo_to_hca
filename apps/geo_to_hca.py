import os
import sys
import xml.etree.ElementTree as xm
from time import sleep

import pandas as pd
import requests as rq
from openpyxl import Workbook
from openpyxl import load_workbook
from openpyxl.utils.cell import get_column_letter
from pysradb.sraweb import SRAweb

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
    def __init__(self, response: rq.Response, accession_list: list):
        self.response = response
        self.accessions = accession_list
        self.error = self.parse_xml_error()

    def parse_xml_error(self):
        root = xm.fromstring(self.response.content)
        return root.find('ERROR').text  # Return the string for the error returned by Efetch

    def __str__(self):
        accession_string = '\n'.join(self.accessions)
        return (f"\nStatus code of the request: {self.response.status_code}.\n"
                f"Error as returned by SRA:\n{self.error}"
                f"The provided accessions were:\n{accession_string}\n\n")


class SraUtils:

    @staticmethod
    def sra_accession_from_geo(geo_accession: str):
        
        sleep(0.5)
        srp = SRAweb().gse_to_srp(geo_accession)
        return srp

    @staticmethod
    def srp_metadata(srp_accession: str) -> pd.DataFrame:
        
        sleep(0.5)
        srp_metadata_url = f'http://trace.ncbi.nlm.nih.gov/Traces/sra/sra.cgi?' \
                           f'save=efetch&db=sra&rettype=runinfo&term={srp_accession}'
        return pd.read_csv(srp_metadata_url)

    @staticmethod
    def srr_fastq(srr_accessions):
        
        sleep(0.5)
        srr_metadata_url = rq.get(f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch/'
                                  f'fcgi?db=sra&id={",".join(srr_accessions)}')
        if srr_metadata_url.status_code == 400:
            raise NotFoundSRA(srr_metadata_url, srr_accessions)
        return xm.fromstring(srr_metadata_url.content), srr_metadata_url.content

    @staticmethod
    def srr_experiment(srr_accession):
        
        sleep(0.5)
        srr_experiment_url = rq.get(f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch/'
                                    f'fcgi?db=sra&id={srr_accession}')
        if srr_experiment_url.status_code == 400:
            raise NotFoundSRA(srr_experiment_url, srr_accession)
        return xm.fromstring(srr_experiment_url.content)

    @staticmethod
    def srr_biosample(biosample_accession):
        
        sleep(0.5)
        srr_biosample_url = rq.get(f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch/'
                                   f'fcgi?db=biosample&id={biosample_accession}')
        if srr_biosample_url.status_code == 400:
            raise NotFoundSRA(srr_biosample_url, biosample_accession)
        return xm.fromstring(srr_biosample_url.content)

    @staticmethod
    def srp_bioproject(bioproject_accession):
        
        sleep(0.5)
        srp_bioproject_url = rq.get(f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch/'
                                    f'fcgi?db=bioproject&id={bioproject_accession}')
        if srp_bioproject_url.status_code == 400:
            raise NotFoundSRA(srp_bioproject_url, bioproject_accession)
        return xm.fromstring(srp_bioproject_url.content)

    @staticmethod
    def pubmed_id(project_pubmed_id):
        
        sleep(0.5)
        pubmed_url = rq.get(f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch/'
                            f'fcgi?db=pubmed&id={project_pubmed_id}&rettype=xml')
        if pubmed_url.status_code == 400:
            raise NotFoundSRA(pubmed_url, project_pubmed_id)
        return xm.fromstring(pubmed_url.content)


def fetch_srp_accession(geo_accession: str):
    
    srp = SraUtils.sra_accession_from_geo(geo_accession)
    if isinstance(srp, pd.DataFrame):
        if not srp.empty:
            assert(len(srp) == 1)
            srp = srp.iloc[0]["study_accession"]
        else:
            srp = "srp not found"
    else:
        srp = "srp not found"
    return srp


def fetch_srp_metadata(srp_accession: str) -> pd.DataFrame:
    
    srp_metadata_df = SraUtils.srp_metadata(srp_accession)
    return srp_metadata_df


def fetch_fastq_names(srr_accessions):
    
    xml_content, content = SraUtils.srr_fastq(srr_accessions)
    fastq_map = {}
    for experiment_package in parse_xml(xml_content):
        fastq_map = retrieve_fastq_from_experiment(fastq_map, experiment_package, content)
    if len(fastq_map) == 0:
        result = "fastq not found"
    else:
        result = "fastq found"
    return fastq_map, result


def fetch_biosample(biosample_accession: str):

    xml_content = SraUtils.srr_biosample(biosample_accession)
    attribute_list = list()
    biosample = xml_content.find('BioSample')
    for description in biosample.findall('Description'):
        sample_title = description.find('Title').text
    for attribute_set in biosample.findall('Attributes'):
        for attribute in attribute_set:
            attribute_list.append(attribute.text)
    return sample_title, attribute_list


def fetch_library_protocol(srr_accession: str):

    xml_content = SraUtils.srr_experiment(srr_accession)
    for experiment_package in parse_xml(xml_content):
        for experiment in experiment_package.find('EXPERIMENT'):
            library_descriptors = experiment.find('LIBRARY_DESCRIPTOR')
            if library_descriptors:
                library_construction_protocol = library_descriptors.find('LIBRARY_CONSTRUCTION_PROTOCOL').text
    return library_construction_protocol


def fetch_sequencing_protocol(srr_accession: str):

    library_construction_protocol = fetch_library_protocol(srr_accession)
    xml_content = SraUtils.srr_experiment(srr_accession)
    for experiment_package in parse_xml(xml_content):
        for experiment in experiment_package.find('EXPERIMENT'):
            illumina = experiment.find('ILLUMINA')
            if illumina:
                instrument = illumina.find('INSTRUMENT_MODEL').text
    return library_construction_protocol, instrument


def fetch_bioproject(bioproject_accession: str):

    # Obtain metadata
    xml_content = SraUtils.srp_bioproject(bioproject_accession)
    bioproject_metadata = xml_content.find('DocumentSummary')

    # Parse metadata to get project information
    project_name = bioproject_metadata.find("Project").find('ProjectDescr').find('Name').text
    project_title = bioproject_metadata.find("Project").find('ProjectDescr').find('Title').text
    project_description = bioproject_metadata.find("Project").find('ProjectDescr').find('Description').text
    project_publication = bioproject_metadata.find("Project").find('ProjectDescr').find('Publication')
    if project_publication.find('DbType').text == 'Pubmed' or project_publication.find('DbType').text == 'ePubmed':
        project_pubmed_id = project_publication.find('Reference').text
    else:
        project_pubmed_id = ''
    return project_name, project_title, project_description, project_pubmed_id


def fetch_pubmed(project_pubmed_id: str):

    xml_content = SraUtils.pubmed_id(project_pubmed_id)
    author_list = list()
    grant_list = list()
    title = xml_content.find("PubmedArticle").find("MedlineCitation").find("Article").find("ArticleTitle").text
    authors = xml_content.find("PubmedArticle").find("MedlineCitation").find("Article").find("AuthorList")
    if authors:
        for author in authors:
            author_list.append([author.find("LastName").text, author.find("ForeName").text,
                                author.find("Initials").text, author.find('AffiliationInfo').find("Affiliation").text])
    grants = xml_content.find("PubmedArticle").find("MedlineCitation").find("Article").find("GrantList")
    if grants:
        for grant in grants:
            grant_list.append([grant.find("GrantID").text, grant.find("Agency").text])
    articles = xml_content.find('PubmedArticle').find('PubmedData').find('ArticleIdList')
    if articles:
        for article_id in articles:
            if "/" in article_id.text:
                article_doi_id = article_id.text
    return title, author_list, grant_list, article_doi_id


def parse_xml(xml_content):

    for experiment_package in xml_content.findall('EXPERIMENT_PACKAGE'):
        yield experiment_package


def extract_read_information(general_read_values):

    reads = {}
    read_info_list = general_read_values.strip().split('--')[1:]
    for read_info in read_info_list:
        read_info = read_info.strip()
        split_read = read_info.split("=")
        reads[split_read[0]] = split_read[1]
    return reads


def retrieve_fastq_from_experiment(fastq_map, experiment_package):
    for run_set in experiment_package.findall('RUN_SET'):
        for run in run_set.findall('RUN'):
            run_attributes = run.findall('RUN_ATTRIBUTES')
            for run_attribute in run_attributes:
                # More than one attribute and they all have the same tag
                for attributes in run_attribute.findall('RUN_ATTRIBUTE'):
                    if attributes.find('TAG').text == 'options':
                        fastq_map[run.attrib['accession']] = extract_read_information(attributes.find('VALUE').text)
    return fastq_map


def initialise(srp_metadata):
    count = 1
    cell_suspension = list(srp_metadata['Experiment'])[0]
    run = list(srp_metadata['Run'])[0]
    lane_index = 1
    process_id = 'process_1'
    return count, cell_suspension, run, lane_index, process_id


def get_process_id(row, process_id, cell_suspension):
    count = int(process_id.split("process_")[1])
    if row['Experiment'] == cell_suspension:
        process_id = process_id
    else:
        count += 1
        process_id = 'process_' + str(count)
    return process_id


def get_lane_index(row, cell_suspension, run, lane_index):
    if row['Experiment'] == cell_suspension and row['Run'] == run:
        lane_index = lane_index
    elif row['Experiment'] == cell_suspension and row['Run'] != run:
        lane_index += 1
    elif row['Experiment'] != cell_suspension:
        lane_index = 1
    return lane_index


def get_row(row, file_index, process_id, lane_index, fastq_map):
    new_row = row
    if not fastq_map:
        new_row['fastq_name'] = ''
    else:
        new_row['fastq_name'] = fastq_map[row['Run']][file_index]
    if "read1" in file_index:
        new_row['fastq_file'] = "index1"
    elif "read2" in file_index:
        new_row['fastq_file'] = "read1"
    elif "read3" in file_index:
        new_row['fastq_file'] = "read2"
    new_row['process_id'] = process_id
    new_row['lane_index'] = lane_index
    return new_row


def integrate_metadata(srp_metadata, fastq_map):
    srp_df = pd.DataFrame()
    count, cell_suspension, run, lane_index, process_id = initialise(srp_metadata)
    for index, row in srp_metadata.iterrows():
        process_id = get_process_id(row, process_id, cell_suspension)
        lane_index = get_lane_index(row, cell_suspension, run, lane_index)
        new_row = get_row(row, 'read1PairFiles', process_id, lane_index, fastq_map)
        srp_df = srp_df.append(new_row, ignore_index=True)
        new_row = get_row(row, 'read2PairFiles', process_id, lane_index, fastq_map)
        srp_df = srp_df.append(new_row, ignore_index=True)
        new_row = get_row(row, 'read3PairFiles', process_id, lane_index, fastq_map)
        srp_df = srp_df.append(new_row, ignore_index=True)
    return srp_df


def get_empty_df(workbook, tab_name):
    sheet = workbook[tab_name]
    values = sheet.values
    empty_df = pd.DataFrame(values)
    cols = empty_df.loc[0, ]
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


def get_sequence_file_tab_xls(srp_df, workbook, tab_name):
    tab = get_empty_df(workbook, tab_name)
    for index, row in srp_df.iterrows():
        tab = tab.append({'sequence_file.file_core.file_name': row['fastq_name'],
                          'sequence_file.file_core.format': 'fastq.gz',
                          'sequence_file.file_core.content_description.text': 'DNA sequence',
                          'sequence_file.read_index': row['fastq_file'],
                          'sequence_file.lane_index': row['lane_index'],
                          'sequence_file.insdc_run_accessions': row['Run'],
                          'process.insdc_experiment.insdc_experiment_accession': row['Experiment'],
                          'cell_suspension.biomaterial_core.biomaterial_id': row['Experiment'],
                          'library_preparation_protocol.protocol_core.protocol_id': '',
                          'sequencing_protocol.protocol_core.protocol_id': '',
                          'process.process_core.process_id': row['process_id']}, ignore_index=True)
    return tab


def get_cell_suspension_tab_xls(srp_df, workbook, tab_name):
    tab = get_empty_df(workbook, tab_name)
    experiments_dedup = list(set(list(srp_df['Experiment'])))
    for experiment in experiments_dedup:
        biosample = list(srp_df.loc[srp_df['Experiment'] == experiment]['BioSample'])[0]
        tab = tab.append({'cell_suspension.biomaterial_core.biomaterial_id': experiment,
                          'specimen_from_organism.biomaterial_core.biomaterial_id': biosample,
                          'cell_suspension.biomaterial_core.ncbi_taxon_id':
                              list(srp_df.loc[srp_df['Experiment'] == experiment]['TaxID'])[0],
                          'cell_suspension.genus_species.text':
                              list(srp_df.loc[srp_df['Experiment'] == experiment]['ScientificName'])[0],
                          'cell_suspension.biomaterial_core.biosamples_accession': biosample}, ignore_index=True)
    write_to_wb(workbook, tab_name, tab)


def get_specimen_from_organism_tab_xls(srp_df, workbook, tab_name):
    tab = get_empty_df(workbook, tab_name)
    samples_dedup = list(set(list(srp_df['BioSample'])))
    for biosample_accession in samples_dedup:
        sample_title, attribute_list = fetch_biosample(biosample_accession)
        tab = tab.append({'specimen_from_organism.biomaterial_core.biomaterial_id': biosample_accession,
                          'specimen_from_organism.biomaterial_core.biomaterial_name': sample_title,
                          'specimen_from_organism.biomaterial_core.biomaterial_description': ','.join(attribute_list),
                          'specimen_from_organism.biomaterial_core.ncbi_taxon_id':
                              list(srp_df.loc[srp_df['BioSample'] == biosample_accession]['TaxID'])[0],
                          'specimen_from_organism.genus_species.text':
                              list(srp_df.loc[srp_df['BioSample'] == biosample_accession]['ScientificName'])[0],
                          'specimen_from_organism.genus_species.ontology_label':
                              list(srp_df.loc[srp_df['BioSample'] == biosample_accession]['ScientificName'])[0],
                          'specimen_from_organism.biomaterial_core.biosamples_accession': biosample_accession,
                          'specimen_from_organism.biomaterial_core.insdc_sample_accession':
                              list(srp_df.loc[srp_df['BioSample'] == biosample_accession]['Sample'])[0],
                          'collection_protocol.protocol_core.protocol_id': ''}, ignore_index=True)
    write_to_wb(workbook, tab_name, tab)


def get_library_protocol_tab_xls(srp_df, workbook, tab_name):
    tab = get_empty_df(workbook, tab_name)
    experiments_dedup = list(set(list(srp_df['Experiment'])))
    count = 0
    library_protocol_set = list()
    library_protocol_dict = {}

    for experiment in experiments_dedup:
        library_protocol = fetch_library_protocol(experiment)

        if library_protocol not in library_protocol_set:
            count += 1
            library_protocol_id = "library_protocol_" + str(count)
            library_protocol_set.append(library_protocol)
            tmp_dict = {
                        'library_preparation_protocol.protocol_core.protocol_id': library_protocol_id,
                        'library_preparation_protocol.protocol_core.protocol_description': library_protocol,
                        'library_preparation_protocol.input_nucleic_acid_molecule.text': 'polyA RNA',
                        'library_preparation_protocol.nucleic_acid_source': 'single cell'
                       }

            if "10X" in library_protocol:
                if "v.2" or "v2" in library_protocol:
                    tmp_dict.update({'library_preparation_protocol.cell_barcode.barcode_read': 'Read1',
                                     'library_preparation_protocol.cell_barcode.barcode_offset': 0,
                                     'library_preparation_protocol.cell_barcode.barcode_length': 16,
                                     'library_preparation_protocol.library_construction_method.text':
                                         "10X 3' v2 sequencing",
                                     'library_preparation_protocol.library_construction_kit.retail_name':
                                         "Single Cell 3’ Reagent Kit v2",
                                     'library_preparation_protocol.library_construction_kit.manufacturer':
                                         "10X Genomics",
                                     'library_preparation_protocol.end_bias': '3 prime tag',
                                     'library_preparation_protocol.primer': 'poly-dT',
                                     'library_preparation_protocol.strand': 'first',
                                     'library_preparation_protocol.umi_barcode.barcode_read': 'Read1',
                                     'library_preparation_protocol.umi_barcode.barcode_offset': 16,
                                     'library_preparation_protocol.umi_barcode.barcode_length': 10
                                     })

                elif "v.3" or "v3" in library_protocol:
                    tmp_dict.update({'library_preparation_protocol.cell_barcode.barcode_read': '',
                                     'library_preparation_protocol.cell_barcode.barcode_offset': '',
                                     'library_preparation_protocol.cell_barcode.barcode_length': '',
                                     'library_preparation_protocol.library_construction_method.text':
                                         "10X 3' v3 sequencing",
                                     'library_preparation_protocol.library_construction_kit.retail_name':
                                         "Single Cell 3’ Reagent Kit v3",
                                     'library_preparation_protocol.library_construction_kit.manufacturer':
                                         "10X Genomics",
                                     'library_preparation_protocol.end_bias': "",
                                     'library_preparation_protocol.primer': "",
                                     'library_preparation_protocol.strand': "",
                                     'library_preparation_protocol.umi_barcode.barcode_read': "",
                                     'library_preparation_protocol.umi_barcode.barcode_offset': "",
                                     'library_preparation_protocol.umi_barcode.barcode_length': ""
                                     })
                else:
                    tmp_dict.update({'library_preparation_protocol.library_construction_method.text': "10X sequencing",
                                     'library_preparation_protocol.library_construction_kit.manufacturer':
                                         "10X Genomics"
                                     })
            tab = tab.append(tmp_dict, ignore_index=True)
        else:
            tab = tab
        if library_protocol in library_protocol_set:
            tab = tab
        library_protocol_dict[experiment] = ""
    write_to_wb(workbook, tab_name, tab)
    return library_protocol_dict


def get_sequencing_protocol_tab_xls(srp_df, workbook, tab_name):
    tab = get_empty_df(workbook, tab_name)
    experiments_dedup = list(set(list(srp_df['Experiment'])))
    count = 0
    instrument_set = list()
    method_set = list()
    sequencing_protocol_dict = {}
    for experiment in experiments_dedup:
        library_construction_protocol, instrument = fetch_sequencing_protocol(experiment)
        if "10X" in library_construction_protocol:
            paired_end = 'no'
            method = 'tag based single cell RNA sequencing'
        elif "10X" not in library_construction_protocol:
            paired_end = ''
            method = ''
        if instrument not in instrument_set or method not in method_set:
            count += 1
            sequencing_protocol_id = "sequencing_protocol_" + str(count)
            instrument_set.append(instrument)
            method_set.append(method)
            tab = tab.append({'sequencing_protocol.protocol_core.protocol_id': sequencing_protocol_id,
                              'sequencing_protocol.instrument_manufacturer_model.text': instrument,
                              'sequencing_protocol.paired_end': paired_end,
                              'sequencing_protocol.method.text': method}, ignore_index=True)
        if instrument in instrument_set and method in method_set:
            tab = tab
        sequencing_protocol_dict[experiment] = ''
    write_to_wb(workbook, tab_name, tab)
    return sequencing_protocol_dict


def update_sequence_file_tab_xls(sequence_file_tab, library_protocol_dict, sequencing_protocol_dict, workbook,
                                 tab_name):
    library_protocol_id_list = list()
    sequencing_protocol_id_list = list()
    for index, row in sequence_file_tab.iterrows():
        library_protocol_id_list.append(library_protocol_dict[row["cell_suspension.biomaterial_core.biomaterial_id"]])
        sequencing_protocol_id_list.append(
            sequencing_protocol_dict[row["cell_suspension.biomaterial_core.biomaterial_id"]])

    sequence_file_tab['library_preparation_protocol.protocol_core.protocol_id'] = library_protocol_id_list
    sequence_file_tab['sequencing_protocol.protocol_core.protocol_id'] = sequencing_protocol_id_list
    write_to_wb(workbook, tab_name, sequence_file_tab)


def get_project_main_tab_xls(srp_df, workbook, geo_accession, tab_name):
    tab = get_empty_df(workbook, tab_name)
    bioproject = list(set(list(srp_df['BioProject'])))
    if len(bioproject) > 1:
        print("more than 1 bioproject, check this")
    else:
        bioproject = bioproject[0]
    project_name, project_title, project_description, project_pubmed_id = fetch_bioproject(bioproject)
    tab = tab.append({'project.project_core.project_title': project_title,
                      'project.project_core.project_description': project_description,
                      'project.geo_series_accessions': geo_accession}, ignore_index=True)
    write_to_wb(workbook, tab_name, tab)


def get_project_publication_tab_xls(srp_df, workbook, tab_name):
    tab = get_empty_df(workbook, tab_name)
    bioproject = list(set(list(srp_df['BioProject'])))
    if len(bioproject) > 1:
        print("more than 1 bioproject, check this")
    else:
        bioproject = bioproject[0]
    project_name, project_title, project_description, project_pubmed_id = fetch_bioproject(bioproject)
    title, author_list, grant_list, article_doi_id = fetch_pubmed(project_pubmed_id)
    name_list = list()
    for author in author_list:
        name = author[0] + ' ' + author[2] + "||"
        name_list.append(name)
    tab = tab.append({'project.publications.authors': ''.join(name_list),
                      'project.publications.title': title,
                      'project.publications.doi': article_doi_id,
                      'project.publications.pmid': project_pubmed_id,
                      'project.publications.url': ''}, ignore_index=True)
    write_to_wb(workbook, tab_name, tab)


def get_project_contributors_tab_xls(srp_df, workbook, tab_name):
    tab = get_empty_df(workbook, tab_name)
    bioproject = list(set(list(srp_df['BioProject'])))
    if len(bioproject) > 1:
        print("more than 1 bioproject, check this")
    else:
        bioproject = bioproject[0]
    project_name, project_title, project_description, project_pubmed_id = fetch_bioproject(bioproject)
    title, author_list, grant_list, article_doi_id = fetch_pubmed(project_pubmed_id)
    for author in author_list:
        name = author[1] + ',,' + list(author)[0]
        affiliation = author[3]
        tab = tab.append({'project.contributors.name': name, 'project.contributors.institution': affiliation},
                         ignore_index=True)
    write_to_wb(workbook, tab_name, tab)


def get_project_funders_tab_xls(srp_df, workbook, tab_name):
    tab = get_empty_df(workbook, tab_name)
    bioproject = list(set(list(srp_df['BioProject'])))
    if len(bioproject) > 1:
        print("more than 1 bioproject, check this")
    else:
        bioproject = bioproject[0]
    project_name, project_title, project_description, project_pubmed_id = fetch_bioproject(bioproject)
    title, author_list, grant_list, article_doi_id = fetch_pubmed(project_pubmed_id)
    for grant in grant_list:
        tab = tab.append({'project.funders.grant_id': grant[0], 'project.funders.organization': grant[1]},
                         ignore_index=True)
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


def main():

    # read a list of geo accessions from a file
    geo_accession_list = pd.read_csv("docs/geo_accessions.txt", sep="\t")

    # initialise dictionary to summarise results
    results = {}

    # For each line of geo accessions:
    for geo_accession in list(geo_accession_list["geo_accession"]):

        # Deal with superseries and more than one accession in a line
        if ',' in geo_accession:
            geo_accession = get_superseries_from_gse(geo_accession.split(',')[0])

        geo_accession = return_gse_from_superseries(geo_accession)
        superseries = geo_accession if isinstance(geo_accession, str) else geo_accession[0]
        if ';' in geo_accession:
            gse_list = geo_accession.split(',')
            superseries = gse_list[0].split(';')[1]
            geo_accession = [gse.split(';')[0] for gse in gse_list]

        # create a new output file name to store the hca converted metadata
        out_file = f"spreadsheets/{superseries}.xlsx"

        # load an empty template HCA metadata excel spreadsheet. All tabs and fields should be in this template.
        workbook = load_workbook(filename="docs/hca_template.xlsx")

        if isinstance(geo_accession, str):
            geo_accession = [geo_accession]

        for accession in geo_accession:
            print(f"processing GEO dataset {accession}")
            ########################################################################################################
            # Ticket created: create a new hca_template which is compatible with ingest row number requirements;   #
            # update all functions to account for the modified template format.                                    #
            ########################################################################################################

            srp_metadata = fetch_srp_metadata(srp_accession)

            # fetch the SRA study accession given the geo accession
            try:
                srp_accession = fetch_srp_accession(accession)
            # Deal with sraweb package doing a sys.exit(1) if it doesn't find the accession
            except SystemExit:
                continue
            #########################################################################################################
            # Ticket created: investigate and add function to deal with cases where "No results found for GSEnnnnnn"#
            # is returned and the script is exited.                                                                 #
            ########################################################################################################

            # fetch the sequencing fastq file names for read1, read2, index files
            fastq_map, result = fetch_fastq_names(list(srp_metadata['Run']))
            if result == "fastq not found":
                results[accession].update({"fastq files available": "no"})
            # if an empty dataframe is returned, skip this geo accession and move to next accession in the file.
            if srp_accession == "srp not found":
                results[accession] = {"SRA Study available": "no"}
                results[accession].update({"fastq files available": "na"})
                continue
                ########################################################################################################
                # Ticket created: investigate and add function to deal with cases where returned dataframe is empty.   #
                ########################################################################################################

            else:

                results[accession].update({"fastq files available": "yes"})
                # Integrate metadata and fastq file names into a single dataframe
                srp_df = integrate_metadata(srp_metadata, fastq_map)

                # Get as much metadata as possible for the different HCA entities
                sequence_file_tab = get_sequence_file_tab_xls(srp_df, workbook, tab_name="Sequence file")

                get_cell_suspension_tab_xls(srp_df, workbook, out_file, tab_name="Cell suspension")

                get_specimen_from_organism_tab_xls(srp_df, workbook, out_file, tab_name="Specimen from organism")

                library_protocol_dict = get_library_protocol_tab_xls(srp_df, workbook, out_file,
                                                                     tab_name="Library preparation protocol")

                sequencing_protocol_dict = get_sequencing_protocol_tab_xls(srp_df, workbook, out_file,
                                                                           tab_name="Sequencing protocol")

                update_sequence_file_tab_xls(sequence_file_tab, library_protocol_dict, sequencing_protocol_dict,
                                             workbook, out_file, tab_name="Sequence file")
                ########################################################################################################
                # Ticket created: functionality not complete; library prep. protocol and sequencing protocol ids are   #
                # currently stored as ''. Need to get correct id per experiment using library_protocol_dict and        #
                # sequencing_protocol_dict.                                                                            #
                ########################################################################################################

                # Project metadata
                get_project_main_tab_xls(srp_df, workbook, geo_accession, out_file, tab_name="Project")

                get_project_publication_tab_xls(srp_df, workbook, out_file, tab_name="Project - Publications")

                get_project_contributors_tab_xls(srp_df, workbook, out_file, tab_name="Project - Contributors")

                get_project_funders_tab_xls(srp_df, workbook, out_file, tab_name="Project - Funders")

        # Make the spreadsheet more readable by deleting all the unused OPTIONAL_TABS and unused linked protocols
        delete_unused_worksheets(workbook)

        # Done
        workbook.save(out_file)

    # Print results and save them
    results = pd.DataFrame.from_dict(results).transpose()
    print(results)
    results.to_csv("docs/results_geo_accessions-testing.txt", sep="\t")


if __name__ == "__main__":
    main()
