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

bad_categories = {
    'Genomic': {
        "code": 'Genomics', 
        "display": "Genomics"
    },
    'Transcriptomic': {
        "code": 'Transcriptomics',
        "display": 'Transcriptomics'
    },
    "WGS": {
        "code": "WGS",
        "display": "Whole Genome Sequencing"
    }
}



def exec(args = None):
    if args is None:
        args = sys.argv[1:]
    host_config = get_host_config()
    # Just capture the available environments to let the user
    # make the selection at runtime
    env_options = sorted(host_config.keys())
    
    parser = ArgumentParser(
        description="Patch the DocumentReference resources to reflect the "
                    "desired categories"
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
        default="output/categories_replaced.json",
        type=FileType('rt'),
        help="Where to write the categories that were found (and patched)."
    )
    parser.add_argument(
        "--category",
        default=None,
        choices=bad_categories.keys(),
        help=f"Category to update if you don't want to change all of them"
    )
    args = parser.parse_args()

    fhir_client = FhirClient(host_config[args.host])

    modified_resources = {}

    for category in bad_categories.keys():
        updated_code = bad_categories[category]

        replacements = {
            "original_code": category,
            "new_code": updated_code['code'],
            "new_display": updated_code['display'],
            "replacements": []
        }

        print(f"DocumentReference?category={category}")
        response = fhir_client.get(f"DocumentReference?category={category}")
        print(f"{category} has {len(response.entries)} resources to be fixed")

        if response.success():
            changes = 0
            for entity in response.entries:
                id = entity['resource']['id']
                categories = entity['resource']['category']
                replacements['replacements'].append({
                    "id": id,
                    "category": deepcopy(categories)
                })
                do_change = False
                for cat in categories:
                    #pdb.set_trace()
                    for coding in cat['coding']:
                        if coding['code'] == category:
                            coding['code'] = updated_code['code']
                            coding['display'] = updated_code['display']
                            do_change = True
                
                if do_change:
                    changes += 1
                    operation = [{
                        "op": "add",
                        "path": "/category",
                        "value": categories
                    }]
                    response = fhir_client.patch("DocumentReference", id, operation)
                    #pdb.set_trace()
                    if response['status_code'] > 299:
                        print(f"Status Code: {response['status_code']}")
                        #pdb.set_trace()
            print(f"{changes} {category}s were changed.")
        modified_resources[category] = replacements

    print(args.log.name)
    try:
        replacement_log = json.load(args.log)
    except:
        replacement_log = {}
        print("Creating new result log")
        args.log = open("output/categories_replaced.json", "wt")
        args.log.close()
    replacement_log[f"{args.host}.{datetime.now().strftime('%Y%m%d')}"] = modified_resources

    with open(args.log.name, 'wt') as inf:
        json.dump(replacement_log, inf, indent=2)
if __name__=='__main__':
    exec()