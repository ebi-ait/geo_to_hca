## geo_to_hca
A tool to assist in the automatic conversion of geo metadata to hca metadata standard.

## Installation

    pip install geo-to-hca
    
## Description
The tool takes as input a single GEO accession or list of GEO accessions and a template HCA metadata excel spreadsheet. It returns as output a pre-filled HCA metadata spreadsheet for each accession. Each spreadsheet can then be used as an intermediate file for completion by manual curation. Optionally an output log file can also be generated which lists the availability of an SRA study accession and fastq file names for each GEO accession given as input.

## Usage

To run it as a package, after installing it via pip:


```shell script
$ geo-to-hca -h                                                            
usage: geo-to-hca [-h] [--accession ACCESSION]
                  [--accession_list ACCESSION_LIST] [--input_file INPUT_FILE]
                  [--nthreads NTHREADS] [--template TEMPLATE]
                  [--header_row HEADER_ROW] [--input_row1 INPUT_ROW1]
                  [--output_dir OUTPUT_DIR] [--output_log OUTPUT_LOG]

optional arguments:
  -h, --help            show this help message and exit
  --accession ACCESSION
                        accession (str): either GEO or SRA accession
  --accession_list ACCESSION_LIST
                        accession list (comma separated)
  --input_file INPUT_FILE
                        optional path to tab-delimited input .txt file
  --nthreads NTHREADS   number of multiprocessing processes to use
  --template TEMPLATE   path to an HCA spreadsheet template (xlsx)
  --header_row HEADER_ROW
                        header row with HCA programmatic names
  --input_row1 INPUT_ROW1
                        HCA metadata input start row
  --output_dir OUTPUT_DIR
                        path to output directory; if it does not exist, the
                        directory will be created
  --output_log OUTPUT_LOG
                        True/False: should the output result log be created
```

To run it as a python module:

```shell script 
cd /path-to/geo_to_hca
python -m geo_to_hca.geo_to_hca -h
```

### Basic arguments: 1 of these options is required. No more than 1 option can be given.

Option (1): Get the HCA metadata for 1 GEO accession

Example command:

`geo-to-hca --accession GSE97168`

Option (2): Get the HCA metadata for a comma-separated list of GEO accessions

Example command:

`geo-to-hca --accession_list GSE97168,GSE124872,GSE126030`

Option (3): Get the HCA metadata given a file consisting of accessions N.B. should consist of an "accession" column name in the header. For example, an example input file named accessions.txt, should look like

```
accession
GSE97168
GSE124872
GSE126030
```

Example command:

`geo-to-hca --input_file <path>/accessions.txt`

### Other optional arguments:

(1)

--template,default="template/hca_template.xlsx"

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


## Developer Notes

### Developing Code in Editable Mode

Using `pip`'s editable mode, projects using geo_to_hca as a dependency can refer to the latest code in this repository 
directly without installing it through PyPI. This can be done either by manually cloning the code
base:

    pip install -e path/to/geo_to_hca

or by having `pip` do it automatically by providing a reference to this repository:

    pip install -e \
    git+https://github.com/ebi-ait/geo_to_hca.git\
    #egg=geo-to-hca
    
    
### Publish to PyPI

1. Create PyPI Account through the [registration page](https://pypi.org/account/register/).
    
   Take note that PyPI requires email addresses to be verified before publishing.

2. Package the project for distribution.
 
        python setup.py sdist
    
3. Install [Twine](https://pypi.org/project/twine/)

        pip install twine        
    
4. Upload the distribution package to PyPI. 

        twine upload dist/*
        
    Running `python setup.py sdist` will create a package in the `dist` directory of the project
    base directory. 
    

