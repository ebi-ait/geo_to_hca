# geo_to_hca
A tool to assist in the automatic conversion of geo metadata to hca metadata standard.

# Description
This script takes as input a single GEO accession or list of GEO accessions and a template HCA metadata excel spreadsheet. It retrieves the SRA study id for each GEO accession and uses this id to retrieve the study metadata. Relevant metadata is obtained from the SRAdb and input into defined tabs in the template HCA metadata excel spreadsheet. The output is a pre-filled HCA metadata spreadsheet which can be used as a starting point for further manual curation. Optionally an output log file can also be generated which lists the availability of an SRA study accession and fastq file names for each GEO accession given as input.

# Running the geo_to_hca.py script

option (1): get the HCA metadata for 1 GEO accession

python apps/geo_to_hca.py --accession

option (2): get the HCA metadata for a comma-separated list of GEO accessions

python apps/geo_to_hca.py --accession_list GSE97168,GSE124872,GSE126030

option (3): get the HCA metadata for a tab-delimited file consisting of accessions N.B. should consist of an "accession"                   column name in the header. See example input file: docs/example_accessions.txt.

python apps/geo_to_hca.py --input_file docs/example_accessions.txt

Other optional arguments:

--template,default="docs/hca_template.xlsx",help='path to an HCA spreadsheet template (xlsx)')
--header_row,type=int,default=4,help='header row with HCA programmatic names')
--input_row1,type=int,default=6,help='HCA metadata input start row')
--output_dir,default='spreadsheets/',help='path to output directory; if it does not exist, the directory will be created')
--output_log,type=bool,default=True,help='True/False: should the output result log be created')
