#!/usr/bin/env python

from wstlr import get_host_config
from pathlib import Path
import json
from ncpi_fhir_client.fhir_client import FhirClient
from ncpi_fhir_client import fhir_auth
from yaml import safe_load
import sys
from argparse import ArgumentParser, FileType
from datetime import datetime
from copy import deepcopy

import pdb

"""This script simply iterates over all Specimen looking for 
situations where type.text is "Whole Blood" and replaces it
with "Peripheral Whole Blood"

"""




def exec(args = None):
    if args is None:
        args = sys.argv[1:]
    host_config = get_host_config()
    # Just capture the available environments to let the user
    # make the selection at runtime
    env_options = sorted(host_config.keys())
    
    parser = ArgumentParser(
        description="Patch the Specimen resources to add Peripheral "
                    "to any type.text entries with only Whole Blood"
    )
    parser.add_argument(
        "--host",
        choices=env_options,
        help=f"Remote configuration to be used to access the FHIR server. "
            "If no environment is provided, the system will stop after "
            "generating the whistle output (no validation, no loading)",
    )
    parser.add_argument(
        "--log",
        default=None,
        type=FileType('rt'),
        help="Where to write the categories that were found (and patched)."
    )
    args = parser.parse_args()

    fhir_client = FhirClient(host_config[args.host])

    modified_resources = {}

    # For now, I'm thinking this only applies to HTP data
    url = f"Specimen?_tag=HTP"
    print(url)
    response = fhir_client.get(url)
    print(f"{len(response.entries)} resources to considered")

    replacements = {
        "original_value": "Whole blood",
        "new_value": "Peripheral Whole Blood",
        "replacements": []
    }
    if response.success():
        changes = 0
        for entity in response.entries:
            id = entity['resource']['id']

            specimen_type = entity['resource']['type']
            if specimen_type['text'] == "Whole blood":
                replacements['replacements'].append({
                    "id": id,
                    "type": deepcopy(specimen_type)
                })

                specimen_type['text'] = "Peripheral Whole Blood"

                changes += 1
                operation = [{
                    "op": "add",
                    "path": "/type",
                    "value": specimen_type
                }]
                
                response = fhir_client.patch("Specimen", id, operation)
                if response['status_code'] > 299:
                    print(f"Status Code: {response['status_code']}")
                    #pdb.set_trace()
        print(f"{changes} 'Whole blood's were changed.")
        modified_resources["Whole blood"] = replacements

    try:
        replacement_log = json.load(args.log)
    except:
        replacement_log = {}
        print("Creating new result log")
        args.log = open("output/whole_bloods_replaced.json", "wt")
        args.log.close()
    replacement_log[f"{args.host}.{datetime.now().strftime('%Y%m%d')}"] = modified_resources

    with open(args.log.name, 'wt') as inf:
        json.dump(replacement_log, inf, indent=2)
if __name__=='__main__':
    exec()