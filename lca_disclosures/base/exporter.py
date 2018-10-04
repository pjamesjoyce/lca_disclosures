import json
import os


class BaseExporter(object):

    _folder_path = None

    @property
    def folder_path(self):
        return self._folder_path

    @folder_path.setter
    def folder_path(self, value):
        if self._folder_path is not None:
            raise AttributeError('value already set')
        self._folder_path = value

    def _prepare_efn(self):
        """
        Return the evaluated file name for the disclosure
        :return:
        """
        raise NotImplemented

    def _prepare_disclosure(self):
        """
        Compute the disclosure and return it as three lists and three sets of sparse matrix 3-tuples (COO)
        :return: fg_flows, bg_flows, emissions, Af, Ad, Bf
        """
        raise NotImplemented

    @property
    def efn(self):
        return self._prepare_efn()

    @property
    def data(self):
        d_i, d_ii, d_iii, d_iv, d_v, d_vi = self._prepare_disclosure()

        p = len(d_i)
        n = len(d_ii)
        m = len(d_iii)

        # collate the data
        data = {
            'foreground flows': d_i,
            'Af': {'shape': [p, p], 'data': d_iv},
            'background flows': d_ii,
            'Ad': {'shape': [n, p], 'data': d_v},
            'foreground emissions': d_iii,
            'Bf': {'shape': [m, p], 'data': d_vi}
        }

        return data

    def write(self, folder_path=None):

        folder_path = folder_path or self.folder_path

        if folder_path is not None:

            if not os.path.isdir(folder_path):
                os.mkdir(folder_path)

            full_efn = os.path.join(folder_path, self.efn)

        else:
            full_efn = self.efn

        with open(full_efn, 'w') as f:
            json.dump(self.data, f)

        return full_efn
