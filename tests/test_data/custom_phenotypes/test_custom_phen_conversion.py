import os
import csv
import pytest
from tretools.utility.custom_phen_conversion import process_custom_codelist

@pytest.fixture
def input_file_path(tmp_path):
    input_file = tmp_path / "input_file.csv"
    content = """phenotype,code,term,name,comment
GNH0001_AtrialFibrillationFlutter,I480,ICD10,Paroxysmal atrial fibrillation,
GNH0001_AtrialFibrillationFlutter,I481,ICD10,Persistent atrial fibrillation,
GNH0001_AtrialFibrillationFlutter,5370000,SNOMED,Atrial flutter,
GNH0001_AtrialFibrillationFlutter,49436004,SNOMED,Atrial fibrillation,
GNH0002_CoronaryArteryDisease_narrow,K403,OPCS4,Saphenous vein graft replacement of three coronary arteries,
GNH0002_CoronaryArteryDisease_narrow,K404,OPCS4,Saphenous vein graft replacement of four or more coronary arteries,
GNH0002_CoronaryArteryDisease_narrow,K411,OPCS4,Autograft replacement of one coronary artery NEC,
Primary_malignancy_mesothelioma,115232000,SNOMED,"[M]Mesothelioma, unspecified",
Primary_malignancy_mesothelioma,254645002,SNOMED,Malignant mesothelioma of pleura,
Primary_malignancy_oesophageal,C15,ICD10,Malignant neoplasm of oesophagus,
"""
    input_file.write_text(content)
    return input_file

def test_process_custom_codelist(input_file_path, tmp_path):
    output_directory = tmp_path
    output_prefix = "customs"

    process_custom_codelist(input_file_path, output_directory, output_prefix)

    # Verify the 3 generated files and their contents
    expected_content = {
        "customs_ICD10.csv": """code,term
I480,GNH0001_AtrialFibrillationFlutter
I481,GNH0001_AtrialFibrillationFlutter
C15,Primary_malignancy_oesophageal
""",
        "customs_SNOMED.csv": """code,term
5370000,GNH0001_AtrialFibrillationFlutter
49436004,GNH0001_AtrialFibrillationFlutter
115232000,Primary_malignancy_mesothelioma
254645002,Primary_malignancy_mesothelioma
""",
        "customs_OPCS4.csv": """code,term
K403,GNH0002_CoronaryArteryDisease_narrow
K404,GNH0002_CoronaryArteryDisease_narrow
K411,GNH0002_CoronaryArteryDisease_narrow
"""
    }

    for file_name, expected_content_str in expected_content.items():
        file_path = os.path.join(output_directory, file_name)
        assert os.path.exists(file_path)

        with open(file_path, 'r') as csvfile:
            content = csvfile.read()
            assert content.strip() == expected_content_str.strip()