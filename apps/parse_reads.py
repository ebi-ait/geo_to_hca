"""
Import required modules.
"""
import xml.etree.ElementTree as xm
import pandas as pd

import sra_utils

"""
Define functions.
"""
def extract_reads_ENA(ftp_path: str) -> []:
    """
    Function to extract single fastq file names from a string containing multiple fastq file paths.
    """
    try:
        read_files = ftp_path.split(';')
        read_files = [file.split("/")[-1] for file in read_files]
    except:
        read_files = []
    return read_files

def parse_xml_SRA(xml_content: object) -> object:
    """
    Gets all the experiment packages from an xml file containing read info.
    """
    for experiment_package in xml_content.findall('EXPERIMENT_PACKAGE'):
        yield experiment_package

def extract_reads_SRA(read_values:str,accession:str,fastq_map:{}) -> {}:
    """
    Function to extract a list of fastq file names from a str containing multiple file paths associated
    with a single run accession.
    """
    if "--read1PairFiles" not in read_values or "--read2PairFiles" not in read_values:
        return fastq_map
    else:
        read_info_list = read_values.strip().split('--')[1:]
        for read_info in read_info_list:
            read_info = read_info.strip()
            split_read = read_info.split("=")
            if 'fastq.gz' in split_read[1]:
                if accession in fastq_map.keys():
                    fastq_map[accession].append(split_read[1])
                else:
                    fastq_map[accession] = [split_read[1]]
    return fastq_map

def get_file_names_from_SRA(experiment_package: object) -> {}:
    """
    Gets fastq file names from an xml returned from SRA following a request with a list
    of run accessions.
    """
    fastq_map = {}
    run_set = experiment_package.find('RUN_SET')
    for run in run_set:
        try:
            accession = run.attrib['accession']
            run_attributes = run.find('RUN_ATTRIBUTES')
            for attribute in run_attributes:
                if attribute.find('TAG').text == 'options':
                    read_values = attribute.find('VALUE').text
                    fastq_map = extract_reads_SRA(read_values,accession,fastq_map)
        except:
            continue
    return fastq_map

def get_fastq_from_SRA(srr_accessions: []) -> {}:
    """
    Function to parse the xml output following a request for run accession metadata to the NCBI SRA database.
    A list of SRA run accessions is given as input to the request. The fastq file paths are extracted from
    this xml and the file names are added to a dictionary with the associated run accessions as keys (fastq_map).
    """
    xml_content = SraUtils.request_fastq_from_SRA(srr_accessions)
    if not xml_content:
        fastq_map = None
    else:
        experiment_packages = parse_xml_SRA(xml_content)
        for experiment_package in experiment_packages:
            try:
                fastq_map = get_file_names_from_SRA(experiment_package)
            except:
                continue
    return fastq_map

def get_lane_index(file: str) -> str:
    """
    Looks for a lane index inside a fastq file name and returns the lane index if found.
    """
    result = re.search('_L[0-9]{3}', file)
    return result

def get_file_index(file: str) -> str:
    """
    Looks for a read index inside a fastq file name (R1,R2,I1,etc.). Returns the read index if found.
    """
    if "_I1" in file or "_R3" in file or "_3" in file:
        ind = 'index1'
    elif "_R1" in file or "_1" in file:
        ind = 'read1'
    elif "_R2" in file or "_2" in file:
        ind = 'read2'
    elif "_I2" in file or "_R4" in file or "_4" in file:
        ind = 'index2'
    else:
         ind = ''
    return ind
