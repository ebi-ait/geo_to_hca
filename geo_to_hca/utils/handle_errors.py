import xml.etree.ElementTree as xm

from geo_to_hca import config


class NotFoundInSRAException(Exception):
    """
    Sub-class for Exception to handle 400 error status codes.
    """
    def __init__(self, response, accession_list):
        self.response = response
        self.accessions = accession_list
        self.error = self.parse_xml_error()

    def parse_xml_error(self):
        root = xm.fromstring(self.response.content)
        if root.find('ERROR') is not None:
            return root.find('ERROR').text
        elif root.find('.//error') is not None:
            return root.find('.//error').text  # Return the string for the error returned by Efetch
        elif root.find('.//Error') is not None:
            return root.find('.//Error').text  # Return the string for the error returned by Efetch
        else:
            return 'error n/a'
    def __str__(self):
        if len(self.accessions) > 1:
            accession_string = '\n'.join(self.accessions)
        else:
            accession_string = self.accessions
        return (f"\nStatus code of the request: {self.response.status_code}.\n"
                f"Error as returned by SRA:\n{self.error}\n"
                f"The provided accessions were:\n{accession_string}\n\n")

    @staticmethod
    def check_efetch_response(efetch_response_xml):
        err_elements = ['error', 'Error']
        return [e.text for e in [efetch_response_xml.find(f'.//{e}') for e in err_elements] if e is not None]


class NotFoundInENAException(Exception):
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
    return NoStudyForGeoAccession(f"Could not find an an object with accession type SRP associated with "
                      f"the given accession {geo_accession}. "
                      f"Go to {config.NCBI_WEB_HOST}/geo/query/acc.cgi?acc={geo_accession} and if possible, find "
                      f"the related study accession, and run the tool with it.")


class TermNotFoundException(RuntimeError):
    def __init__(self, term, error_key, db='sra'):
        self.error_key = error_key
        self.term = term
        self.db = db

    def __str__(self):
        return f'Term {self.term} not found in {self.db}. ' \
               f'Esearch error: {self.error_key}. ' \
               f'Check if this accession exists and is public at {config.EUTILS_HOST}/{self.db}?term={self.term}'

class NoStudyForGeoAccession(RuntimeError):
    pass
