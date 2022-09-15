#!/usr/bin/env python

"""
Pierrette has provided a single model which should represent a comprehensive 
data-dictionary, but we need to split it out into corresponding "tables". 

This script will take the output of my fake-dd.py script and annotate those
table-based DD with the appropriate pieces from her model and alert me when
something in the table DD doesn't align properly with the expected model.   

input: 
    table-dd.csv (output from fake-dd )
    portal_schema.csv (pierrette's model)

"""

import csv

import pdb

from wstlr import die_if
from argparse import ArgumentParser, FileType
from pathlib import Path

parser = ArgumentParser(description="Annotate fake-dd output with details "
                        "from Pierrette's Portal Model csv")

parser.add_argument("table_dd",
                    type=FileType('rt'),
                    nargs='+',
                    help="One ore more output files from fake-dd. Multiple "
                        "files will be annotated independently.")

parser.add_argument("-o",
                    "--output", 
                    default="data/dd/",
                    help="Directory where new files are written (default "
                        "data/dd/)")

parser.add_argument("-p",
                    "--portal-model",
                    type=FileType('rt'),
                    default="data/dd-base/portal_schema.csv",
                    help="The source for portal model annotations. ")

args = parser.parse_args()

class PortalAnnotation:
    """Each var from the portal schema is represented as one of these"""
    def __init__(self, row):
        self.varname = row['Attribute']
        self.description = row['Description']
        self.valid_values = [x.strip() for x in row['Valid Values'].split(",")]
        if self.valid_values == ['']:
            self.valid_values = []

annotations = {}
for line in csv.DictReader(args.portal_model):
    pan = PortalAnnotation(line)

    annotations[pan.varname] = pan

outpath = Path(args.output)
outpath.mkdir(parents=True, exist_ok=True)

for dd in args.table_dd:
    dd_name = Path(dd.name).stem
    out_filename = outpath / f"{dd_name}.csv"
    with out_filename.open('wt') as outf:
        writer = csv.writer(outf)

        ddinput = csv.DictReader(dd)
        header = ddinput.fieldnames

        writer.writerow(header)

        for line in ddinput:
            ann = annotations[line['varname']]

            line['vardesc'] = ann.description
            if len(ann.valid_values) > 0:
                line['values'] = ";".join(ann.valid_values)
            else:
                line['values'] = ""

            writer.writerow([line[x] for x in header])








    
