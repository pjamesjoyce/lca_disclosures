from ..flow_types import ForegroundFlow, BackgroundFlow, EmissionFlow


class UnobservedFragmentFlow(Exception):
    pass


class KeyCollision(Exception):
    pass


class ObservedFlow(object):
    """
    An ObservedFlow is an abstract class for an exchange that is observed to be part of some disclosure.  An observed
    flow has a KEY, which identifies it uniquely among all observed flows, and it has a PARENT, which is itself either
    the singleton ReferenceFlow, RX, or an existing ObservedFlow from the disclosure foreground.  The parent indicates
    the column to which the observation belongs, and the key indicates the row.

    ObservedFlows have several properties that must be implemented in subclasses:
     - parent --> the node in the graph from which the exchange is observed.
     - flow --> the flow entity.  Assumed to have 'Name' property and unit() method
     - direction --> relative to parent.
     - locale --> where the observation occurred
     - value --> the quantity of the exchange, relative to a unit activity of the parent

    In addition, ObservedFlows have optional descriptive keys that are used depending on where the flow fits into the
    disclosure:
     - bg_key --> Background exchanges should return a 3-tuple of term_node, term_flow, direction (w.r.t. term node)
     - context --> Emission exchanges should return a context tuple

    The ObservedFlow implements some standard methods:
     - observe(parent): assign the parent node to an observed flow (use the singleton RX to observe a reference flow).
     - emission_key: flow, direction, locale, context
     - cutoff_key: the first 3 of emission_key

    """
    _parent = None

    @property
    def parent(self):
        if self._parent is None:
            raise UnobservedFragmentFlow
        return self._parent

    @property
    def key(self):
        """
        Every observed flow needs a distinct key that enables it to be retrieved unambiguously.
        :return:
        """
        raise NotImplemented

    @property
    def bg_key(self):
        """
        OF subclass must be further subclassed to define bg_key
        must return 3-tuple: term_node, term_flow, direction; all from the perspective of the referenced background
        :return:
        """
        raise TypeError

    @property
    def context(self):
        """
        Return a context tuple.
        This should get implemented for any class that implements emission_key
        :return:
        """
        raise TypeError

    @property
    def emission_key(self):
        return self.flow, self.direction, self.locale, self.context

    @property
    def cutoff_key(self):
        return tuple(self.emission_key[:3])

    @property
    def flow(self):
        raise NotImplemented

    @property
    def direction(self):
        raise NotImplemented

    @property
    def locale(self):
        raise NotImplemented

    @property
    def value(self):
        raise NotImplemented

    @property
    def external_ref(self):
        """
        This is only used for Foreground flows
        :return:
        """
        raise NotImplemented

    def observe(self, parent):
        """
        A new observed flow must be "observed" from the perspective of an existing flow, which becomes the parent
        :param parent:
        :return:
        """
        self._parent = parent


class ReferenceFlow(ObservedFlow):
    @property
    def key(self):
        return None

    @property
    def value(self):
        return 1.0


'''
Singleton for use in marking the reference flow of a fragment.
'''
RX = ReferenceFlow()


class SeqList(object):
    def __init__(self):
        self._l = []
        self._d = {}

    def index(self, key):
        if key not in self._d:
            ix = len(self._l)
            self._l.append(key)
            self._d[key] = ix

        return self._d[key]

    def __len__(self):
        return len(self._l)

    def __getitem__(self, key):
        try:
            return self._l[key]
        except TypeError:
            return self._d[key]

    def to_list(self):
        return self._l


class SeqDict(object):
    """
    Current theory is that this is basically just a SeqList-- operational difference seems to be, when we add to
    _fg we __setitem__, which will throw a key error if the key already exists; whereas with the others we index(),
    which adds if new, returns if existing.
    """
    def __init__(self):
        self._l = []
        self._d = {}
        self._ix = {}

    def __setitem__(self, key, value):
        if key in self._d:
            raise KeyError('Value for %s already set!' % key)
        ix = len(self._l)
        self._l.append(key)
        self._d[key] = value
        self._ix[value] = ix
        self._ix[key] = ix

    def __len__(self):
        return len(self._l)

    def __getitem__(self, key):
        try:
            return self._d[key]
        except KeyError:
            return self._d[self._l[key]]

    def index(self, item):
        return self._ix[item]

    def to_list(self):
        return [self._d[x] for x in self._l]


class Observer(object):
    def __init__(self, quiet=False):
        """
        These are really 'list-dicts' where they have a sequence but also a reverse-lookup capability.
        functionality tbd
        """
        self._quiet = quiet

        self._fg = SeqDict()  # log the flow entities we encounter; map key to OFF
        self._co = SeqList()  # map index to (flow, direction)
        self._bg = SeqList()  # map index to (process_ref, term_flow)
        self._em = SeqList()  # map index to (flow, direction)

        self._Af = []  # list of OFFs
        self._Ac = []  # list of cutoffs  (get appended to Af)
        self._Ad = []  # list of OBGs
        self._Bf = []  # list of emissions

        self._key_lookup = dict()  # map ff key to type-specific (map, key)

    def _print(self, *args):
        if not self._quiet:
            print(*args)

    def __iter__(self):
        return self

    def __next__(self):
        raise NotImplemented

    def __getitem__(self, key):
        _map, _key = self._key_lookup[key]
        return _map[_key]

    def __setitem__(self, key, value):
        if key in self._key_lookup:
            raise KeyCollision(key)
        self._key_lookup[key] = value

    def _show_mtx(self, mtx):
        tag = {'Af': 'Foreground',
               'Ac': 'Cutoffs',
               'Ad': 'Background',
               'Bf': 'Emissions'}[mtx]  # KeyError saves
        if mtx != 'Af':
            print('\n')
        print('%s - %s' % (mtx, tag))
        for k in getattr(self, '_' + mtx):
            print(k)

    def show(self):
        self._show_mtx('Af')
        self._show_mtx('Ac')
        self._show_mtx('Ad')
        self._show_mtx('Bf')

    def _add_foreground(self, off):
        """
        Creates a new node from the most recent OFF
        :param off: the observed fragment flow
        :return:
        """
        self._print('Handling as FG')
        self._fg[off.key] = off  # we __setitem__ for _fg
        self[off.key] = (self._fg, off.key)
        self._Af.append(off)

    def _add_background(self, obg):
        """

        :param obg: an Observed background
        :return:
        """
        self._print('Handling as BG')
        ix = self._bg.index(obg.bg_key)  # we index() for the other types
        self[obg.key] = (self._bg, ix)
        self._Ad.append(obg)

    def _add_cutoff(self, oco, extra=''):
        """

        :param oco: the Observed Cutoff
        :return:
        """
        self._print('Adding Cutoff %s' % extra)
        ix = self._co.index(oco.cutoff_key)
        self[oco.key] = (self._co, ix)
        self._Ac.append(oco)

    def _add_emission(self, oem):
        """

        :param oem: the Observed Emission.  Must have: key, context, cutoff_key, emission_key
        :return:
        """
        if oem.context is None or len(oem.context) == 0:
            self._print('Emission with null context --> cutoff')
            self._add_cutoff(oem, extra='emission with null context')
        else:
            self._print('Adding Emission')
            ix = self._em.index(oem.emission_key)
            self[oem.key] = (self._em, ix)
            self._Bf.append(oem)

    @property
    def functional_unit(self):
        return self._fg[0]

    def generate_disclosure(self):
        _ = [x for x in self]  # ensure fully iterated
        p = len(self._fg)

        d_i = [ForegroundFlow(off.flow['Name'], off.direction, off.flow.unit(), location=off.locale,
                              external_ref=off.external_ref)
               for off in self._fg.to_list()]  # this returns an ObservedForegroundFlow
        d_i += [ForegroundFlow(flow['Name'], dirn, flow.unit(), location=locale, external_ref=flow.external_ref)
                for flow, dirn, locale in self._co.to_list()]

        d_ii = [BackgroundFlow(node.origin, flow['Name'], dirn, flow.unit(),
                               activity=node.external_ref,
                               location=node['SpatialScope'],
                               external_ref=flow.external_ref)
                for node, flow, dirn in self._bg.to_list()]

        d_iii = [EmissionFlow(flow.origin, flow['Name'], dirn, flow.unit(),
                              context='; '.join(context),
                              location=locale,
                              external_ref=flow.external_ref)
                 for flow, dirn, locale, context in self._em.to_list()]

        d_iv = []
        d_v = []
        d_vi = []

        for off in self._Af:
            if off.parent is RX:
                continue
            d_iv.append([[self._fg.index(off.key), self._fg.index(off.parent.key)], off.value])
        for oco in self._Ac:
            d_iv.append([[p + self._co.index(oco.cutoff_key), self._fg.index(oco.parent.key)], oco.value])

        for obg in self._Ad:
            d_v.append([[self._bg.index(obg.bg_key), self._fg.index(obg.parent.key)], obg.value])

        for oem in self._Bf:
            d_vi.append([[self._em.index(oem.emission_key), self._fg.index(oem.parent.key)], oem.value])

        return d_i, d_ii, d_iii, d_iv, d_v, d_vi
