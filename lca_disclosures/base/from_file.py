import os
import json

from .disclosure import BaseDisclosure


class Disclosure(BaseDisclosure):
    """
    For restoring a disclosure from a file
    """
    def __init__(self, extension=None, **kwargs):
        self._ext = extension
        super(Disclosure, self).__init__(**kwargs)

    def _prepare_efn(self):
        return self.filename

    def _prepare_disclosure(self):
        ext = self._ext.lower()
        if ext == '.json':
            return self._disclosure_from_json()
        elif ext.startswith('.xls'):
            return self._disclosure_from_xls()
        else:
            raise ValueError('Unknown file extension %s' % self._ext)

    def _disclosure_from_xls(self):
        raise NotImplementedError

    def _disclosure_from_json(self):
        fname_ext = os.path.join(self.folder_path, self.efn + self._ext)
        with open(fname_ext) as fp:
            j = json.load(fp)

        return j['foreground flows'], j['background flows'], j['foreground emissions'], \
            j['Af']['data'], j['Ad']['data'], j['Bf']['data']


def from_file(input_file):
    """
    Infers type from file extension
    :param input_file:
    :return:
    """
    abspath = os.path.abspath(input_file)
    folder = os.path.dirname(abspath)
    filename, ext = os.path.splitext(os.path.basename(abspath))
    return Disclosure(folder_path=folder, filename=filename, extension=ext)
