from collections import OrderedDict
from rpy2.rinterface import SexpVector, RNULLType
from rpy2.robjects.vectors import Vector
import rpy2.robjects as robjects

from trtools.monkey import patch
import trtools.rpy.conversion as rconv 

def is_null(obj):
    return isinstance(obj, RNULLType)

def rinfo(obj):
    info = OrderedDict()
    info['classes'] = list(obj.rclass)
    if hasattr(obj, 'names') and not is_null(obj.names):
        info['names'] = list(obj.names)
    if hasattr(obj, 'list_attrs') and not is_null(obj.names):
        info['list_attrs'] = list(obj.list_attrs())
        
    return info    

def rrepr(obj):
    print type(obj)
    info = rinfo(obj)
    out = "" 
    for k,vals in info.iteritems():
        out += k + "\n"
        out += "\n".join(["\t"+str(val) for val in vals if val])
        out += "\n"
    return out 

def printr(obj):
    print rrepr(obj)

class RObjectWrapper(object):
    """
        Essentially a class with slightly better repr and easy access to
        attr, names, and slots
    """
    def __init__(self, robj):
        self.robj = robj

    def __repr__(self):
        return rrepr(self.robj)

    def __getattr__(self, name):
        """
            AFAIK, this should be fine as long as there are no name
            clashes. Haven't run into any.
        """
        obj = None
        if name in self.robj.names:
            obj = self.robj.rx2(name)
        if name in self.robj.list_attrs():
            obj = self.robj.do_slot(name)
        if hasattr(self.robj, name):
            obj = getattr(self.robj, name)

        # wrap attribute. 
        if obj is not None: 
            return obj.to_py()
    
        raise AttributeError()

@patch([Vector], 'to_py')
def to_py(o):
    """
        Converts to python object if possible. 
        Otherwise wraps in ROBjectWrapper
    """
    res = None
    try:
        rcls = o.do_slot("class")
    except LookupError, le:
        rcls = []

    if isinstance(o, SexpVector) and len(rcls) > 0:
        if 'xts' in rcls:
            res = rconv.convert_xts_to_df(o)
        elif 'POSIXct' in rcls:
            res = rconv.convert_posixct_to_index(o)
        
    if res is None and isinstance(o, SexpVector):
        res = RObjectWrapper(o)

    if res is None:
        res = o

    return res

def simple_string_vector_repr(self):
    if len(self) == 1:
        return self[0]
    return SexpVector.__old_repr__(self)
    
#SexpVector.__old_repr__ = SexpVector.__repr__
#SexpVector.__repr__ = simple_string_vector_repr
