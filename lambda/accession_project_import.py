from geo_to_hca import geo_to_hca
import re
from ingest.api.ingestapi import IngestApi
from ingest.importer.importer import XlsImporter


def _is_valid_geo_or_insdc_accession(geo_or_srp_accession):
    regex = re.compile('^(GSE|SRP|ERP).*$')
    return bool(regex.match(geo_or_srp_accession))


def lambda_handler(event, context):
    accession = event['accession']
    token = event['Authorization']

    if not _is_valid_geo_or_insdc_accession(accession):
        raise Exception(f'The given accession ({accession}) is invalid.')

    workbook = geo_to_hca.create_spreadsheet_using_accession(accession)

    importer = XlsImporter(IngestApi())
    project_uuid, errors = importer.import_project_from_workbook(workbook, token)

    if errors:
        error_messages = ' ,'.join([e.get('details') for e in errors if e.get('details')])
        raise Exception(f'There were errors in importing the project: {error_messages}.')

    return {
        'message': project_uuid
    }
