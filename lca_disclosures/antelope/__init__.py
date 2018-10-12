from .foreground_observer import ForegroundObserver
from .traversal_observer import TraversalObserver
from .to_excel import to_excel

from lca_disclosures import BaseDisclosure


class _AntelopeDisclosure(BaseDisclosure):
    _observer = None

    def _prepare_efn(self):
        if self.filename is None:
            return str(self._observer.functional_unit)
        return self.filename

    def _prepare_disclosure(self):
        return self._observer.generate_disclosure()


class AntelopeForegroundDisclosure(_AntelopeDisclosure):
    def __init__(self, query, *args, **kwargs):

        self._observer = ForegroundObserver(query, *args)

        super(AntelopeForegroundDisclosure, self).__init__(**kwargs)


class AntelopeTraversalDisclosure(_AntelopeDisclosure):
    def __init__(self, ffs, **kwargs):

        self._observer = TraversalObserver(ffs)

        super(AntelopeTraversalDisclosure, self).__init__(**kwargs)
