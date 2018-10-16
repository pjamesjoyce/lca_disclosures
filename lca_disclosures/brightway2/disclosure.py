import brightway2 as bw
import numpy as np

from ..flow_types import ForegroundFlow, BackgroundFlow, EmissionFlow
from ..base import BaseDisclosure
from ..utils import matrix_to_data


def bw2_to_origin(db_name):
    return '.'.join(['local', 'bw2', db_name])


def origin_to_bw2(origin):
    prefix = 'local.bw2.'
    if origin.startswith(prefix):
        return origin[len(prefix):]
    raise ValueError('Origin does not match BW2 convention')


def reconstruct_matrix(matrix_dict, normalise=False, clear_diagonal=False):
    m = np.zeros(matrix_dict['shape'])
    for (r, c), v in matrix_dict['data']:
        m[r, c] = v

    if normalise and sum(m.diagonal()) != 0:
        m = -m / m.diagonal()

        if clear_diagonal:
            m = m + np.eye(matrix_dict['shape'][0])

    return m


class Bw2Disclosure(BaseDisclosure):

    def __init__(self, project_name, database_name, fu=None, **kwargs):

        self.project_name = project_name
        self.database_name = database_name
        self.origin = bw2_to_origin(database_name)
        self.fu = fu
        super(Bw2Disclosure, self).__init__(**kwargs)

        # self.efn = self._prepare_efn()
        # self.data = self._prepare_disclosure()

    def _prepare_efn(self):

        if isinstance(self.filename, str):
            efn = self.filename
        else:
            efn = '{}_{}'.format(self.project_name.replace(" ", "_"), self.database_name.replace(" ", "_"))

        return efn

    def _prepare_disclosure(self):

        bw.projects.set_current(self.project_name)
        db = bw.Database(self.database_name)
        foreground = [(a['database'], a['code'])for a in db]

        # set fu to be the first item in the foreground matrix
        if self.fu is not None and self.fu in foreground:
            fu_list = [self.fu]
            foreground = fu_list + [x for x in foreground if x not in fu_list]
            
        else:
            temp_foreground = []
            for a in db:
                k = (a['database'], a['code'])
                for x in a.exchanges():
                    if x['input'] in foreground and x['type'] != 'production':
                        temp_foreground.append([(foreground.index(x['input']), foreground.index(k)), x['amount']])
            
            temp_matrix = reconstruct_matrix({'data': temp_foreground, 'shape': (len(foreground), len(foreground))})
            
            fu_list = [x for i, x in enumerate(foreground)
                       if list(temp_matrix.sum(axis=1))[i] == 0 and list(temp_matrix.sum(axis=0))[i] != 0]
            foreground = fu_list + [x for x in foreground if x not in fu_list]
        
        foreground_coords = []
        technosphere = []
        biosphere = []
        techno_coords = []
        bio_coords = []

        for a in db:
            k = (a['database'], a['code'])
            for x in a.exchanges():
                if x['input'] in foreground and x['type'] != 'production':
                    foreground_coords.append([(foreground.index(x['input']), foreground.index(k)), x['amount']])
                elif x['input'] in foreground and x['type'] == 'production':
                    foreground_coords.append([(foreground.index(x['input']), foreground.index(k)), -x['amount']])
                elif x['type'] == 'technosphere':
                    if x['input'] not in technosphere:
                        technosphere.append(x['input'])
                    techno_coords.append([(technosphere.index(x['input']), foreground.index(k)), x['amount']])
                elif x['type'] == 'biosphere':
                    if x['input'] not in biosphere:
                        biosphere.append(x['input'])
                    bio_coords.append([(biosphere.index(x['input']), foreground.index(k)), x['amount']])
                    
        technosphere_info = [bw.Database(x[0]).get(x[1]) for x in technosphere]
        biosphere_info = [bw.Database(x[0]).get(x[1]) for x in biosphere]
        foreground_info = [bw.Database(x[0]).get(x[1]) for x in foreground]

        # for BW2, use database name as origin and database ID as external_ref
        technosphere_flows = [BackgroundFlow(bw2_to_origin(x[0]), technosphere_info[i].get('name', 'n/a'),
                                             'Input',  # need help supporting explicit directions in bw2
                                             technosphere_info[i].get('unit', 'n/a'),
                                             activity=technosphere_info[i].get('activity', 'n/a'),
                                             location=technosphere_info[i].get('location', None),
                                             external_ref=x[1])
                              for i, x in enumerate(technosphere)]

        biosphere_flows = [EmissionFlow(bw2_to_origin(x[0]),
                                        "{}, {}".format(biosphere_info[i]['name'], biosphere_info[i]['type']),
                                        'Output',  # need help supporting explicit directions in bw2
                                        biosphere_info[i]['unit'],
                                        context='; '.join(biosphere_info[i]['categories']),
                                        external_ref=x[1])
                           for i, x in enumerate(biosphere)]

        foreground_flows = [ForegroundFlow(foreground_info[i]['name'],
                                           'Input',  # need help supporting explicit directions in bw2
                                           foreground_info[i]['unit'],
                                           location=foreground_info[i]['location'],
                                           external_ref=x[1])
                            for i, x in enumerate(foreground)]

        # techno_matrix = {'data':techno_coords, 'shape':(len(technosphere),len(foreground))}
        # bio_matrix = {'data':bio_coords, 'shape':(len(biosphere),len(foreground))}
        
        unprocessed_foreground_matrix = {'data': foreground_coords, 'shape': (len(foreground), len(foreground))}
        processed_matrix = reconstruct_matrix(unprocessed_foreground_matrix, normalise=True,  clear_diagonal=True)
        
        foreground_coords = matrix_to_data(processed_matrix)
        # foreground_matrix = {'data':foreground_coords, 'shape':(len(foreground), len(foreground))}

        return foreground_flows, technosphere_flows, biosphere_flows, foreground_coords, techno_coords, bio_coords


"""
        data = {
            'foreground flows':foreground_names,
            'Af':foreground_matrix,
            'background flows': technosphere_names,
            'Ad':techno_matrix,
            'foreground emissions': biosphere_names,
            'Bf':bio_matrix
        }
        
                    
        return data
    def write(self):

        if isinstance(self.filename, str):
            efn = self.filename
        else:
            efn = '{}_{}.json'.format(self.project_name.replace(" ", "_"), self.origin.replace(" ", "_"))
        
        if isinstance(self.folder_path, str):

            if not os.path.isdir(self.folder_path):
                os.mkdir(self.folder_path)

            efn = os.path.join(self.folder_path, efn)

            

        with open(efn, 'w') as f:
            json.dump(self.data, f)

        return efn
"""