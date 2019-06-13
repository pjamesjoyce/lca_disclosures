def check_direction(dirn):
    if isinstance(dirn, str):
        dirn = dirn[0].lower()
    return {0: 'Input',
            1: 'Output',
            'i': 'Input',
            'o': 'Output'}[dirn]


class DisclosedFlow(object):
    """
    A DisclosedFlow is any row in the Af, Ad, or Bf matrix that makes up the disclosure.  The flow must be defined
    at minimum by a name, a direction for which the flow has a positive measure, and its quantitative unit of measure.

    Optional keyword arguments include a location, which is the locale of the node, and and external_ref, which is
    used to make reference to the flow from outside the disclosure.  An external_ref is required to be unique.

    The external_ref becomes mandatory for background flows and emissions, along with a second ref specifying the
    activity or context that "terminates" (i.e. provides the partner to) the exchange.

    Any additional kwargs are appended to the output when the flow is serialized.

    ABOUT DISCLOSED FLOW DIRECTIONS

    Each DisclosedFlow comprises "half" an exchange, specifying one of the partners to the exchange (i.e. the flow's
    index in a particular disclosure list indicates the row of the entry in the corresponding matrix).  The stated
    'direction' is always interpreted with respect to the OTHER partner to the exchange (i.e. the column of the matrix
    entry).  This somewhat counterintuitive convention privileges column-wise reading of exchange data, and enables the
    same sign/direction convention to be used for technosphere flows, cutoff flows, and emissions alike.

    For example, consider a DisclosedFlow with name='magic gas', direction='input', and unit='m3', which appears fifth
    in a list of disclosed flows. Then a matrix entry (row=5, column=0), value=0.1234) means that 0.1234 m3 of magic
    gas travels OUT of the node at row-index 5 and INTO the node at column-index 0 for every for a unit activity of
    node in column 0.  This means that the natural direction for the *reference flow* at node 5 is OUTPUT (i.e. the
    opposite of the direction given in the disclosed flow).  This interpretation is consistent, regardless of whether
    the disclosed flow is part of Af, Ad, or Bf.

    Given a matrix entry ((row, col), value), the direction of the exchange is determined by the row index. A positive
    value indicates that the flow is has the stated direction with respect to the column index; a negative value
    indicates that the flow has the opposite direction with respect to the column.

    In Ecoinvent, all ordinary technosphere flows have direction 'Input', while treatment flows have direction 'Output.'
    Because of the convention is that all reference flows be outputs,on-diagonal entries for treatment flows are
    negated.

    Entirely arbitrarily, integer 0 is considered equivalent to 'Input', and integer 1 is equivalent to 'Output.'

    For Emission flows, the direction is as expected (i.e. 'Output' indicates an emission from the technosphere, while
    'Input' indicates a resource extraction from the environment).

    When a DisclosedFlow is interpreted as a reference flow, the given direction is with respect to the CONSUMER, i.e.
    the direction a flow would have with respect to an exterior column that uses the flow in its own inventory.

    """
    _direction = None
    _flow_type = None
    index = NotImplemented

    def __init__(self, name, direction, unit, location=None, external_ref=None, **kwargs):
        """

        :param name:
        :param direction:
        :param unit:
        :param location:
        :param external_ref:
        :param kwargs:
        """
        self._flow_name = name
        self.direction = direction
        self._unit = unit
        self._location = location
        self._external_ref = external_ref
        self.init_args = kwargs

    @property
    def external_ref(self):
        return self._external_ref or self.full_name

    @property
    def name(self):
        return self._flow_name

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, value):
        try:
            value = check_direction(value)
        except KeyError:
            raise ValueError('Direction must be input (or 0) or output (or 1)')
        self._direction = value

    @property
    def unit(self):
        return self._unit

    @property
    def location(self):
        return self._location

    @property
    def flow_type(self):
        return self._flow_type

    def serialize(self):
        d = {
            'name': str(self.name),
            'unit': str(self.unit),
            'location': str(self.location)
        }
        d.update(self.init_args)
        return d

    @property
    def _disp_locale(self):
        """
        a courteous display of location
        :return:
        """
        if len(self.location) > 0:
            return '[%s] ' % self.location
        else:
            return ''

    @property
    def full_name(self):
        return '%s %s%s (%s)' % (self._flow_name, self._disp_locale, self.unit, self.direction)

    def __hash__(self):
        return hash((self.external_ref, self.direction))

    def __eq__(self, other):
        try:
            oer = other.external_ref
            od = check_direction(other.direction)
        except AttributeError:
            return NotImplemented
        if self.external_ref == oer and self.direction == od:
            return True
        return False


class ForegroundFlow(DisclosedFlow):
    """
    A ForegroundFlow is a flow that is defined by the model being disclosed, i.e. does not refer to anything with a
    fixed meaning outside of the model.

    When a disclosure is published as a semantic resource on the Internet, the location at which the disclosure is
    published becomes the "origin" to which the foreground flows are anchored; otherwise, the foreground flows are
    only locally defined.
    """
    _flow_type = 'foreground'
    _cutoff = None

    def set_cutoff(self):
        self._cutoff = True

    @property
    def cutoff(self):
        if self._cutoff:
            return 'X'

    index = ('name', 'direction', 'unit', 'cutoff', 'location', 'external_ref')


class _SemanticFlow(DisclosedFlow):
    """
    A _SemanticFlow is a flow that corresponds to a single semantic reference, in other words a flow that signifies
    something with 'fixed' or recognized meaning on the Internet.  (e.g. JSON-LD) The characteristic of a semantic flow
    is its "origin", which is ultimately a URL prefix e.g.: 'https://magic-lca-data.vault.lc/ecoinvent/3.4/apos'
    that specifies the originating data source. Current practice is the origin given as a dot-separated hierarchical
    specifier, e.g. 'local.ecoinvent.3.4.apos.bw2'

    The concatenation of a flow's origin and its external_ref with a forward-slash '/' should specify a fully-qualified
    entity specification:
    - local.ecoinvent.3.4.apos/34148d74-9225-46d1-9740-bb03b59f8813 corresponds to Ammonium Sulfate production [RER]
    - local.ecoinvent.3/230d8a0a-517c-43fe-8357-1818dd12997a corresponds to Particulates < 2.5um [kg] [urban air close
    to ground].  (UUID consistent across all ecoinvent v3 database minor versions and system models ?)

    A semantic flow serves to "terminate" a foreground flow, meaning it provides the other partner to the exchange.
    For background flows, this partner is an activity in a separate database.  For emission flows, this partner is
    an environmental context.
    """

    _origin = None
    _termination = None
    _term_type = None

    @property
    def origin(self):
        return self._origin

    @origin.setter
    def origin(self, value):
        if self._origin is not None:
            raise AttributeError('origin already set to %s' % self.origin)
        if len(str(value)) < 1:
            raise TypeError('Origin must be non-empty string')
        self._origin = str(value)

    def __init__(self, origin, *args, _termination=None, external_ref=None, **kwargs):
        self.origin = origin
        if _termination is None or len(_termination) == 0:
            raise TypeError('%s must be specified! cut-off flows remain in foreground' % self._term_type)
        self._termination = _termination
        super(_SemanticFlow, self).__init__(*args, external_ref=external_ref, **kwargs)

    def serialize(self):
        d = super(_SemanticFlow, self).serialize()
        d['origin'] = str(self.origin)
        d[self._term_type] = str(self._termination)
        return d

    def __hash__(self):
        return hash((self.origin, self.external_ref, self.direction, self._termination))

    def __eq__(self, other):
        try:
            oo = other.origin
            oer = other.external_ref
            od = check_direction(other.direction)
        except AttributeError:
            return NotImplemented
        if self.external_ref == oer and self.direction == od and self.origin == oo and hash(self) == hash(other):
            return True
        return False


class BackgroundFlow(_SemanticFlow):
    """
    A background flow is a flow whose environmental characteristics are determined according to a background data
    source that is independently available, and thus does not depend on the foreground being disclosed. Note that the
    background data source does not need to be public or available to any specific reader.  The BackgroundFlow is
    merely a reference to that data source.

    The originating data source should 'terminate' the flow, meaning provide a process with the
    """
    _flow_type = 'background'
    _term_type = 'activity'
    index = ('origin', 'name', 'direction', 'unit', 'activity', 'location', 'external_ref')

    def __init__(self, *args, activity=None, **kwargs):
        """

        :param origin:  string signifying the originating database for characterizing the emission flow
        :param args: name, direction, unit
        :param activity: mandatory external id for the background activity that 'terminates' the flow in the origin db,
         i.e. provides the partner to the exchange
        :param kwargs: external_ref [required], location, other user-significant keywords
        """
        super(BackgroundFlow, self).__init__(*args, _termination=activity, **kwargs)

    @property
    def activity(self):
        return self._termination


class EmissionFlow(_SemanticFlow):
    """
    An Emission Flow is any flow that is exchanged between the model foreground and some environmental context.  This
    includes resource extractions, emissions, and social flows. Cut-off emissions can be considered equivalent to
    cut-off foreground flows.

    For emissions, the direction of the flow should ALWAYS be consistent with the "natural" direction of the named
    context (i.e. should always be 'input' for resource extractions and 'output' for emissions).  Avoided or negative
    flows should be indicated by a negative value for the matrix entry and NEVER by specifying the non-natural
    direction. Ultimately contexts should also be semantic refs and have an agreed-upon direction.
    """
    _flow_type = 'emission'
    _term_type = 'context'
    index = ('origin', 'name', 'direction', 'unit', 'context', 'location', 'external_ref')

    def __init__(self, *args, context=None, **kwargs):
        """

        :param origin:  string signifying the originating database for characterizing the emission flow
        :param args: name, direction, unit
        :param context: string signifying the environmental compartment with which the flow is exchanged - None
         indicates a cutoff emission.
        :param kwargs: location, other user-significant keywords
        """
        super(EmissionFlow, self).__init__(*args, _termination=context, **kwargs)

    @property
    def context(self):
        return self._termination

    @property
    def _disp_context(self):
        """
        This could be endlessly elaborated. i.e. if context.split('; ')[-1] == 'unspecified' we should do something
        :return:
        """
        try:
            return '(%s) ' % self.context.split('; ')[-1]
        except IndexError:
            return ''

    @property
    def full_name(self):
        return '%s %s%s[%s]' % (self._flow_name, self._disp_context, self._disp_locale, self.direction)
