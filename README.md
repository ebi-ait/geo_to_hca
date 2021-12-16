# geo_to_hca
A tool to assist in the automatic conversion of geo metadata to hca metadata standard.

# Description
The apps/geo_to_hca.py script takes as input a single GEO accession or list of GEO accessions and a template HCA metadata excel spreadsheet. It returns as output a pre-filled HCA metadata spreadsheet for each accession. Each spreadsheet can then be used as an intermediate file for completion by manual curation. Optionally an output log file can also be generated which lists the availability of an SRA study accession and fastq file names for each GEO accession given as input.

# How to run the geo_to_hca.py script

# Requirements

See requirements.txt file.

# Basic arguments: 1 of these options is required. No more than 1 option can be given.

Option (1): Get the HCA metadata for 1 GEO accession

Example command:
python apps/geo_to_hca.py --accession GSE97168

Option (2): Get the HCA metadata for a comma-separated list of GEO accessions

Example command:
python apps/geo_to_hca.py --accession_list GSE97168,GSE124872,GSE126030

Option (3): Get the HCA metadata given a file consisting of accessions N.B. should consist of an "accession" column name in the header. For example, an example input file named accessions.txt, should look like

```
accession
GSE97168
GSE124872
GSE126030
```

Example command:
python apps/geo_to_hca.py --input_file <path>/accessions.txt

# Other optional arguments:

(1)

--template,default="docs/hca_template.xlsx"

The default template is an empty HCA metadata spreadsheet in excel format, with the relevant HCA metdata headers in rows 1-5. The default header row with programmatic names is row 4; the default start input row is row 6.
It is not necessary to specify this argument unless the HCA spreadsheet format changes.

(2)

--header_row,type=int,default=4

The default header row with programmatic names is row 4. It is not necessary to specify this argument unless the HCA spreadsheet format changes.

(3)

--input_row1,type=int,default=6

The default start input row is row 6.
It is not necessary to specify this argument unless the HCA spreadsheet format changes.

(4)

--output_dir,default='spreadsheets/'

An output directory can be specified by it's path. If the path does not already exist, it will be created. If this argument
is not given, the default output directory is 'spreadsheets/'

(5)

--output_log,type=bool,default=True

An optional arugment to retrieve an output log file stating whether an SRA study id and fastq file names were available for each GEO accession given as input.
