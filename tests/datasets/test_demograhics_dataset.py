from tretools.datasets.demographic_dataset import DemographicDataset


from datetime import datetime

DEMOGRAPHIC_MAPPING_FILE = "tests/test_data/demographics/mapping.txt"
DEMOGRAPHIC_FILE = "tests/test_data/demographics/gender_dummy.txt"
MAPPING_CONFIG = {
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


def test_demographic_dataset():
    data = DemographicDataset(DEMOGRAPHIC_MAPPING_FILE, DEMOGRAPHIC_FILE)

    assert data.mapped_data.shape == (3, 4)
    assert data.demographics.shape == (3, 11)


def test_demographic_dataset_process():
    data = DemographicDataset(DEMOGRAPHIC_MAPPING_FILE, DEMOGRAPHIC_FILE)
    data.process_dataset(MAPPING_CONFIG)

    assert data.data.shape == (3, 3)


def test_demographic_dataset_process_round_to_day():
    data = DemographicDataset(DEMOGRAPHIC_MAPPING_FILE, DEMOGRAPHIC_FILE)
    data.process_dataset(MAPPING_CONFIG, 9)

    expected_dob = ["1983-10-09", "1979-01-09", "1948-06-09"]
    expected_dob_as_dt = [datetime.strptime(x, "%Y-%m-%d").date() for x in expected_dob]

    assert data.data["dob"].to_list() == expected_dob_as_dt

    