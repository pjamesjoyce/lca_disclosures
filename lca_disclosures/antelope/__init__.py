from .foreground_observer import ForegroundObserver
from .traversal_observer import TraversalObserver


from lca_disclosures import BaseDisclosure


class _AntelopeDisclosure(BaseDisclosure):
    _observer = None

    def _prepare_efn(self):
        if self.filename is None:
            return str(self._observer.functional_unit.flow)
        return self.filename

    def _prepare_disclosure(self):
        return self._observer.generate_disclosure()


class AntelopeForegroundDisclosure(_AntelopeDisclosure):
    def __init__(self, query, *args, quiet=False, **kwargs):

        self._observer = ForegroundObserver(query, *args, quiet=quiet)

        super(AntelopeForegroundDisclosure, self).__init__(**kwargs)


class AntelopeTraversalDisclosure(_AntelopeDisclosure):
    def __init__(self, ffs, quiet=False, **kwargs):

        self._observer = TraversalObserver(ffs, quiet=quiet)

        super(AntelopeTraversalDisclosure, self).__init__(**kwargs)
