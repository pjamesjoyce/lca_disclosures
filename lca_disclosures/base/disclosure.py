import json
import os
import re

from scipy.sparse import coo_matrix, eye
from scipy.sparse.linalg import spsolve
from pandas import ExcelWriter

from ..utils import data_to_coo, matrix_to_excel, meta_to_excel, matrix_to_table


class LcaDisclosureError(Exception):
    pass


class BaseDisclosure(object):

    _origin = None
    _folder_path = None
    _disclosure = None
    _complete = False

    def __init__(self, folder_path=None, filename=None):
        self.folder_path = folder_path
        self.filename = filename
        self._disclosure = self._prepare_disclosure()
        self._mark_cutoffs()
        self._complete = True

    @property
    def complete(self):
        return self._complete

    @property
    def folder_path(self):
        return self._folder_path

    @folder_path.setter
    def folder_path(self, value):
        if self._folder_path is not None:
            raise AttributeError('folder_path already set')
        self._folder_path = value

    @property
    def origin(self):
        return self._origin

    @origin.setter
    def origin(self, value):
        if self._origin is not None:
            raise AttributeError('foreground origin already set: %s' % self._origin)
        self._origin = value

    def _prepare_efn(self):
        """
        Return the evaluated file name for the disclosure.  The filename should be extensionless, so that the extension
        can be added by the export method.
        :return:
        """
        return NotImplemented

    def _prepare_disclosure(self):
        """
        Compute the disclosure and return it as three lists and three sets of sparse matrix tuples.

        The lists should be instances of the appropriate types: ForegroundFlow, BackgroundFlow, EmissionFlow
        The matrices should be given as a nested 2-tuple: ((row, col), data)

        returns a 6-tuple
        :return:
        """
        return NotImplemented

    '''
    Accessing contents of the prepared disclosure
    '''
    @property
    def disclosure(self):
        return self._disclosure

    @property
    def foreground_flows(self):
        return self.disclosure[0]

    @property
    def background_flows(self):
        return self.disclosure[1]

    @property
    def emission_flows(self):
        return self.disclosure[2]

    @property
    def Af(self):
        return self.disclosure[3]

    @property
    def Ad(self):
        return self.disclosure[4]

    @property
    def Bf(self):
        return self.disclosure[5]

    '''
    Derived values
    '''
    def x_tilde(self):
        Af = data_to_coo(self.data['Af']).tocsr()
        p = len(self.foreground_flows)
        b = coo_matrix(([1.0], ([0], [0])), shape=(p, 1))
        return spsolve(eye(p) - Af, b)

    def _mark_cutoffs(self):
        if self.complete:
            return
        fg = set(range(len(self.foreground_flows)))
        for matrix in (self.Af, self.Ad, self.Bf):
            for coords, val in matrix:
                if coords[1] in fg and val != 0:
                    # found a nonzero value: column is not a cutoff
                    fg.remove(coords[1])
        for f in fg:
            self.foreground_flows[f].set_cutoff()

    @property
    def cutoffs(self):
        """
        Generator. Yields disclosed flows that are cutoffs (i.e. foreground flows that have no termination in any
        of the foreground matrices and emissions that have no specified context)
        :return:
        """
        if not self.complete:
            raise LcaDisclosureError('Disclosure is not complete!')
        for ff in self.foreground_flows:
            if ff.cutoff:
                yield ff
        for em in self.emission_flows:
            if em.context is None:  # Note this will throw an error until typed flows are implemented
                yield em

    '''
    IO operations
    '''

    @property
    def efn(self):
        """
        This accessor returns the evaluated filename (without extension)
        :return:
        """
        return self._prepare_efn()

    def _spec_filename(self, filename=None, folder_path=None):
        folder_path = folder_path or self.folder_path

        if filename is None:
            filename = self.efn

        if folder_path is not None:

            if not os.path.isdir(folder_path):
                os.mkdir(folder_path)

            filename = os.path.join(folder_path, filename)
        return filename

    @property
    def data(self):
        """
        This accessor returns the all disclosure data in a dict
        :return:
        """
        d_i, d_ii, d_iii, d_iv, d_v, d_vi = self.disclosure

        p = len(d_i)
        n = len(d_ii)
        m = len(d_iii)

        # collate the data
        data = {
            'disclosure type': self.__class__.__name__,
            'foreground flows': [x.serialize() for x in d_i],
            'Af': {'shape': [p, p], 'data': d_iv},
            'background flows': [x.serialize() for x in d_ii],
            'Ad': {'shape': [n, p], 'data': d_v},
            'foreground emissions': [x.serialize() for x in d_iii],
            'Bf': {'shape': [m, p], 'data': d_vi}
        }

        if self.origin is not None:
            data['origin'] = self.origin

        return data

    def write_json(self, filename=None, folder_path=None, **kwargs):

        filename = self._spec_filename(filename=filename, folder_path=folder_path)

        filename += '.json'

        with open(filename, 'w') as f:
            json.dump(self.data, f, **kwargs)

        return filename

    def write_excel(self, filename=None, folder_path=None, tabular=False):
        filename = self._spec_filename(filename=filename, folder_path=folder_path)

        if not filename.lower().endswith('xlsx'):
            filename += '.xlsx'

        xlw = ExcelWriter(filename)

        fg = ['%d. %s' % (i, ff.full_name) for i, ff in enumerate(self.foreground_flows)]
        bg = [bg.full_name for bg in self.background_flows]
        em = [em.full_name for em in self.emission_flows]

        data = self.data
        Af = data_to_coo(data['Af'])
        Ad = data_to_coo(data['Ad'])
        Bf = data_to_coo(data['Bf'])

        meta_to_excel(xlw, sheetname='foreground', disclosed_flows=self.foreground_flows)
        meta_to_excel(xlw, sheetname='background', disclosed_flows=self.background_flows)
        meta_to_excel(xlw, sheetname='emissions', disclosed_flows=self.emission_flows)

        if tabular:
            matrix_to_table(xlw, sheetname='Af', matrix=Af, row='foreground')
            matrix_to_table(xlw, sheetname='Ad', matrix=Ad, row='background')
            matrix_to_table(xlw, sheetname='Bf', matrix=Bf, row='emission')
        else:
            matrix_to_excel(xlw, sheetname='Af', matrix=Af.todense(), index=fg)
            matrix_to_excel(xlw, sheetname='Ad', matrix=Ad.todense(), index=bg)
            matrix_to_excel(xlw, sheetname='Bf', matrix=Bf.todense(), index=em)

        xt = self.x_tilde()
        ad = Ad * xt
        matrix_to_excel(xlw, sheetname='ad_tilde', matrix=ad, index=bg)

        bf = Bf * xt
        matrix_to_excel(xlw, sheetname='bf_tilde', matrix=bf, index=em)

        xlw.save()

        return filename
