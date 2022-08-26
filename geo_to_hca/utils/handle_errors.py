import os
import xml.etree.ElementTree as xm

"""
Define functions.
"""
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
                f"Error as returned by ENA:\n{self.error}"
                f"The provided project title or name was:\n{self.title}\n\n")


def no_related_study_err(geo_accession):
    return ValueError(f"Could not find an an object with accession type SRP associated with "
                      f"the given accession {geo_accession}. "
                      f"Go to {NCBI_WEB_HOST}/geo/query/acc.cgi?acc={geo_accession} and if possible, find "
                      f"the related study accession, and run the tool with it.")


NCBI_WEB_HOST=os.getenv('NCBI_WEB_HOST', default='https://www.ncbi.nlm.nih.gov')
