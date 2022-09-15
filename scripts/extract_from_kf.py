#!/usr/bin/env python

"""
Extract Specimen and File Meta Data from the file Meen provided
"""
import csv
from collections import defaultdict
import sys

# The DD doesn't include a hint about the type, so we'll have to 
# build a lookup for any non-string types. Categorical have 
# values, so they are typed as String. IDs may or may not be 
# purely numeric, so they are always strings. 
field_type = {
    "Volume": "decimal",
    "Age At Biospecimen Collection": "decimal",
    "Size": "integer"
}

# Few of the categoricals agree with the DD so those pieces
# are falling through the whistle conversion. So, we'll fix them
# here rather than dealing with extra delay.
convert_to_dd = {
    "NA": "",
    "Rseq": "RNAseq",
    "Gene Expression Quantification": "Gene expression quantifications",

}

# This is the file meen loaded into Google and reflects udates from 
# afternoon 9/12
khor_file_meta = "data/kf/meen_khor_manifest_with_age.csv" 

# This is an export of Pierrettes schema. We'll use it to extract
# The right fields into the right files
schema = "data/kf/portal_schema.csv"

tablename_entries = ['Biospecimen','Data File']

# Make sure all of the necessary columns are present
colnames = defaultdict(list)
for table in tablename_entries:
    colnames[table].append("Participant ID")
colnames['Data File'].append("Sample ID")

# We'll build out both DDs based on the contents of this file
with open(schema, 'rt') as f:
    reader = csv.DictReader(f)

    # We need a type for certain DD related tasks
    reader.fieldnames.append("type")

    with open("data/dd/specimen-dd.csv", 'wt') as specf:
        specw = csv.writer(specf)
        specw.writerow(reader.fieldnames)


        with open("data/dd/file_meta_data-dd.csv", 'wt') as fmf:
            fmw = csv.writer(fmf)
            fmw.writerow(reader.fieldnames)

            writers = {
                "Biospecimen": specw,
                "Data File": fmw
            }

            for line in reader:
                if line['Parent'] in tablename_entries:
                    if line['Attribute'] in field_type:
                        line['type'] = field_type[line['Attribute']]
                    else:
                        line['type'] = 'string'

                    colnames[line['Parent']].append(line['Attribute'])
                    writers[line['Parent']].writerow([line[x] for x in reader.fieldnames])
                    

# Start with the Specimen
with open(khor_file_meta, 'rt') as f:
    reader = csv.DictReader(f)
    header = colnames['Biospecimen']

    reader.fieldnames[0] = 'KFID'
    reader.fieldnames[1] = 'Participant ID'
    reader.fieldnames = [x.lower() for x in reader.fieldnames]

    # Avoid duplicate rows
    observed_ids = set()

    with open("data/tables/BRI-DSR/specimen.csv", 'wt') as outf:
        writer = csv.writer(outf)
        writer.writerow(header)

        for line in reader:
            row_data = []

            if line['sample id'] not in observed_ids:
                observed_ids.add(line['sample id'])
                for colname in header:
                    if colname.lower() not in line:
                        print(f"No matching column name: '{colname}'")
                        print("\n\t".join(line.keys()))
                        sys.exit(1)

                    column_name = colname.lower()
                    column_value = line[column_name]
                    # Force the data to conform with the DD so that stuff works
                    if column_value in convert_to_dd:
                        row_data.append(convert_to_dd[column_value])
                    else:
                        row_data.append(column_value)

                writer.writerow(row_data)

# Do Files. We'll need to add sample ID to the 
with open(khor_file_meta, 'rt') as f:
    reader = csv.DictReader(f)
    header = colnames['Data File']

    reader.fieldnames[0] = 'KFID'
    reader.fieldnames[1] = 'Participant ID'
    reader.fieldnames[17] = "Filename"
    reader.fieldnames[18] = "KF Junk Filename"

    with open("data/tables/BRI-DSR/file_meta_data.csv", 'wt') as outf:
        writer = csv.writer(outf)
        writer.writerow(header)

        for line in reader:

            if line['Filename'].strip() not in ["NA", ""]:
                row_data = []

                for colname in header:
                    if colname not in line:
                        print(f"No matching column name: {colname}")
                        sys.exit(1)

                    # Force the data to conform with the DD so that stuff works
                    if line[colname] in convert_to_dd:
                        row_data.append(convert_to_dd[line[colname]])
                    else:
                        row_data.append(line[colname])

                writer.writerow(row_data)
