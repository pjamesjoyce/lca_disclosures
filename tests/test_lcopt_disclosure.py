import os
from lcopt import *

from lca_disclosures.lcopt.disclosure import LcoptDisclosure as DisclosureExporter

def test_lcopt_disclosure():

	fname = os.path.join('assets', 'Test_model.lcopt')

	model = LcoptModel(load=fname, autosetup=False)

	lde = DisclosureExporter(model, parameter_set=0, folder_path='exporter_testing')

	disclosure_file = lde.write_json()

	assert os.path.isfile(disclosure_file)

