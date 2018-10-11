import os
from fixtures import *
from lca_disclosures import from_file, BaseDisclosure

def test_from_file():

    filepath = os.path.join(".", TEST_FOLDER, "{}.json".format(TEST_FILENAME))

    my_disclosure = from_file(filepath)

    assert isinstance(my_disclosure, BaseDisclosure)

    assert my_disclosure.foreground_flows
    assert my_disclosure.background_flows
    assert my_disclosure.emission_flows
    assert my_disclosure.Af
    assert my_disclosure.Ad
    assert my_disclosure.Bf
