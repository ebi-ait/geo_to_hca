# geo_to_hca
Tools to assist in the automatic conversion of geo metadata to hca metadata standard.

# Running apps/geo_to_hca.py (Version 1)
This script takes as input an empty template HCA spreadsheet and a tab-delimited text file listing multiple GEO accessions in the form: GSEnnnnnn. Currently, the script throws errors when given certain GEO accessions as it cannot find an associated SRA study accession to work with; this is something we are in the process of fixing. If you would like to retrieve HCA metadata for a given list of GEO accessions, it is possible to run the script after removing the accessions which are causing the errors. Version 2 is in progress!

# Issues which need addressing:

Issue: implement a function for merging of metadata from multiple GEO accessions associated with 1
       publication (accessions separated in the input file by ',').
        
Issue: create a new hca_template which is compatible with ingest row number requirements;
       update all functions to account for the modified template format.
        
Issue: investigate and add function to deal with cases where "No results found for GSEnnnnnn"
       is returned when pysradb is used to retrieve an SRA study accession (currently the script exits).

Issue: investigate and add function to deal with cases where returned dataframe is empty when pysradb
       is used to retrieve an SRA study accession.

Issue: investigate and add function to deal with cases where fastq file names are not found.

Issue: update Sequence file tab functionality not complete; experiment library prep. protocol and sequencing protocol ids are currently stored as ''. Need to get correct id per experiment and store in library_protocol_dict and sequencing_protocol_dict.
