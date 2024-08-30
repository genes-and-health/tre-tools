#!/usr/bin/env python
# coding: utf-8

# # Run through of TRE Tools
# 
# The following notebook is designed to demonstrate the main features of the tretools package. The notebook is split into the following sections:
# 
# - Codelists
# - Datasets
# - Phenotype Reports
# - Summary Report
# 
# Codelists and Datasets form the building blocks of the system. They come together in specific queries in Phenotype Reports - to answer questions such as which patients in a given dataset have an event that matches a code in given codelist. A phenotype in this context is defined as a person who has a code in an identified codelist. A person might have several codes in 1 dataset, 1 qualifying code in different codelists or multiple codes in multiple codelists. 

# ## Codelists
# First we import our Codelist from a file. Let's start with a SNOMED codelist. 

# In[3]:


from tretools.codelists.codelist import Codelist


# In[51]:

snomed_codelist = Codelist("examples/codelists/disease_a_snomed.csv", codelist_type="SNOMED")


# In[52]:


snomed_codelist.data


# In[53]:


snomed_codelist.codes


# Now lets do the same with an ICD codelist. 

# In[54]:


icd_codelist = Codelist("examples/codelists/disease_a_icd.csv", "ICD10")


# In[55]:


icd_codelist.codes


# Sometimes we want to add X to the end of a ICD10 to allow us to use it in NHS Digital Data. Now lets pass in `add_x_codes` to see the difference. You will see that extra codes are generated with the same code term. 

# In[56]:


icd_codelist_with_x = Codelist("examples/codelists/disease_a_icd.csv", "ICD10", add_x_codes=True)
icd_codelist_with_x.codes


# Additionally, with ICD10 codes, we want to truncate this to 3 digits only. 

# In[57]:


truncated_icd_codelist = Codelist("examples/codelists/disease_a_icd.csv", "ICD10", icd10_3_digit_only=True)
truncated_icd_codelist.codes


# ## Datasets
# 
# There are 3 types of Datasets:
# - RawDataset - this takes in data, which might be messy. It can be processed to produce a ProcessedDataset
# - ProcessedDataset - this is a tidy dataset that can be merged with other ProcessedDataset
# - DemographicDataset - this is a special type of Dataset that can be created from specific data files

# In[58]:


from tretools.datasets.raw_dataset import RawDataset
from tretools.datasets.demographic_dataset import DemographicDataset


# We can load a datafile into a RawDataset. This will put the data at `.data`. 

# In[59]:


raw_data = RawDataset(path="examples/datasets/primary_care_data.csv", coding_system="SNOMED", dataset_type="primary_care")


# In[60]:


raw_data.data


# There are different dates, some missing data and an extra column. Let's get rid of these. We pass in a deduplication option, plus the maps of the column. This will create a ProcessedDataset.

# In[61]:


gp_processed_data = raw_data.process_dataset(
    deduplication_options=["nhs_number", "code", "date"], 
    column_maps={"original_code": "code", "original_term": "term", "clinical_effective_date": "date", "pseudo_nhs_number": "nhs_number"}
)


# In[62]:


gp_processed_data.data


# Now you will see that there is a clean dataset. 
# 
# Let's move onto Demographics. 

# In[63]:


demographics = DemographicDataset(path_to_mapping_file="examples/demographics/mapping.txt", path_to_demographic_file="examples/demographics/gender_dummy.txt")


# Similar to RawDataset, we can process this data to standardise it. We need to pass in a map of what columns mean in each of the 2 input files.  

# In[64]:


mapping_config = {
    "mapping": {
        "OrageneID": "study_id",
        "PseudoNHS_2023-11-08": "nhs_number"
    },
    "demographics": {
        "S1QST_Oragene_ID": "study_id",
        "S1QST_MM-YYYY_ofBirth": "dob",
        "S1QST_Gender": "gender"
    }
}


# In[65]:


demographics.process_dataset(mapping_config)


# In[66]:


demographics.data


# We now have a clean dataset for age and gender. 

# # Phenotype Report

# In[67]:


from tretools.phenotype_report.report import PhenotypeReport


# We create an empty report. 

# In[68]:


report = PhenotypeReport("Disease A")


# We now add counts. A count includes the following fields:
# 
# - Dataset (compulsory)
# - Codelist (compulsory)
# - Demographics (optional)

# In[69]:


report.add_count("primary_care", codelist=snomed_codelist, dataset=gp_processed_data, demographics=demographics)


# This gives us a count summary. 

# In[70]:


report.counts


# We can add a further count. Let's use a different dataset - one from barts to do this. 

# In[71]:


barts_data = RawDataset("examples/datasets/barts_diagnosis.tab", dataset_type="barts_health", coding_system="ICD10")
processed_data_hospital = barts_data.process_dataset(deduplication_options=["nhs_number", "code", "date"],
                           column_maps={
                               "ICD_Diagnosis_Cd": "code", 
                               "ICD_Diag_Desc": "term", 
                               "Activity_date": "date", 
                               "PseudoNHS_2023_04_24": "nhs_number"}
                           )


# In[72]:


report.add_count("secondary_care", codelist=icd_codelist, dataset=processed_data_hospital, demographics=demographics)


# Let's examine our counts now:

# In[73]:


report.counts


# This produces a report that is in its raw form. It can be used by SummaryReportTransformer for now but in the future, more report transformer types will be added. The advantage of this, is that a phenotype report can run once but be used for many outputs. 
# 
# # Summary Report

# In[74]:


from tretools.report_transformers.summary_report import SummaryReportTransformer


# We put our reports into a list. 

# In[75]:


reports = [report]


# We create our SummaryReportTransformer() from the reports, and then transform the output. We must pass in a path where we want the summary to be created. 

# In[76]:


summary_report = SummaryReportTransformer.load_from_objects(reports)


# In[77]:


summary_report.transform(path="summary_report")


# This should output a number of folders and files contain your report at that path. 
