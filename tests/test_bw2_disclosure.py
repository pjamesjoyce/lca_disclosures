import os
import brightway2 as bw2
from fixtures import *

from lca_disclosures.brightway2.disclosure import Bw2Disclosure as DisclosureExporter
from lca_disclosures.brightway2.importer import DisclosureImporter

def test_attributes():

    de = DisclosureExporter(TEST_BW_PROJECT_NAME, TEST_BW_DB_NAME, folder_path=TEST_FOLDER, filename=TEST_FILENAME)

    assert de.foreground_flows
    assert de.background_flows
    assert de.emission_flows
    assert de.Af
    assert de.Ad
    assert de.Bf

def test_bw2_disclosure():
    
    de = DisclosureExporter(TEST_BW_PROJECT_NAME, TEST_BW_DB_NAME, folder_path=TEST_FOLDER, filename=TEST_FILENAME)

    disclosure_file = de.write_json()

    print (os.path.realpath(disclosure_file))

    assert os.path.isfile(disclosure_file)

    bw2.projects.set_current(IMPORT_PROJECT_NAME)

    di = DisclosureImporter(disclosure_file)

    di.apply_strategies()

    assert di.statistics()[2] == 0

    di.write_database()

    assert len(bw2.Database(di.db_name)) != 0
