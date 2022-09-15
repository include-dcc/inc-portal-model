
# This assumes we have valid links for each of the tables inside data that point
# to wherever we extracted those tables
scripts/split_dataset.py data/study.csv data/participant.csv data/condition.csv

# Build a harmony file containing contents of the Data Dictionary and terms 
# found inside the cohort condition file.
scripts/build_harmony_file.py -c data/condition.csv data/dd/*-dd.csv