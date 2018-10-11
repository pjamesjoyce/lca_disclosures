import pytest
import os
import shutil
import brightway2 as bw2
from tests.assets.test_database import TEST_MODEL_DATABASE
from tests.fixtures import *

DEFAULT_BIOSPHERE_PROJECT = "LCOPT_Setup_biosphere" # This makes the tests run quicker on machines set up for lcopt

FULL_SETUP = True

def bw2_project_exists(project_name):
    return project_name in bw2.projects


@pytest.fixture(scope="session", autouse=True)
def setup_fixtures(request):

    print('RUNNING SETUP FIXTURE')
    
    if FULL_SETUP:
        bw2.projects.purge_deleted_directories()
        if bw2_project_exists(IMPORT_PROJECT_NAME):
            bw2.projects.delete_project(name=IMPORT_PROJECT_NAME, delete_dir=True)
        if bw2_project_exists(TEST_BW_PROJECT_NAME):
            bw2.projects.delete_project(name=TEST_BW_PROJECT_NAME, delete_dir=True)

        if bw2_project_exists(DEFAULT_BIOSPHERE_PROJECT):
            bw2.projects.set_current(DEFAULT_BIOSPHERE_PROJECT)
            bw2.projects.copy_project(IMPORT_PROJECT_NAME, switch=True)
        else:
            bw2.projects.set_current(IMPORT_PROJECT_NAME)
            bw2.bw2setup()
        

        script_path = os.path.dirname(os.path.realpath(__file__))
        ecospold_folder = os.path.join("tests", "assets", "datasets")
        ecospold_path = os.path.join(script_path, ecospold_folder)
        print(ecospold_path)

        ei = bw2.SingleOutputEcospold2Importer(ecospold_path, "Ecoinvent3_3_cutoff")
        ei.apply_strategies()
        ei.statistics()
        ei.write_database()

        bw2.projects.copy_project(TEST_BW_PROJECT_NAME, switch=True)

        test_db = bw2.Database(TEST_BW_DB_NAME)
        test_db.write(TEST_MODEL_DATABASE)


        bw2.projects.set_current('default')
    
    def teardown_fixtures():
        print('TEAR IT DOWN!!')

        print('cleaning up brightway')

        bw2.projects.set_current('default')
        
        if bw2_project_exists(TEST_BW_PROJECT_NAME):
            bw2.projects.delete_project(name=TEST_BW_PROJECT_NAME)#, delete_dir=True)
            #bw2.projects.purge_deleted_directories()

        if bw2_project_exists(IMPORT_PROJECT_NAME):
            bw2.projects.delete_project(name=IMPORT_PROJECT_NAME)

        shutil.rmtree(os.path.join(script_path, "tests", TEST_FOLDER))
    
    request.addfinalizer(teardown_fixtures)