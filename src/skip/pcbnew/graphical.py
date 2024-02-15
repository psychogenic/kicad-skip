'''
Created on Feb 15, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from skip.sexp.parser import ParsedValueWrapper, ParsedValue
from skip.pcbnew.layer import LayerPropertyHandler

import logging 
log = logging.getLogger(__name__)

class GraphicalElementWrapper(ParsedValueWrapper):
    def __init__(self, pv:ParsedValue):
        super().__init__(pv)
        self._layer_handler = LayerPropertyHandler(pv.layer, self.parent)

    @property
    def layer(self):
        return self._layer_handler.get()
    
    @layer.setter 
    def layer(self, setTo):
        return self._layer_handler.set(setTo)
    
    
    def __repr__(self):
        coords = None 
        options = ['at', 'center', 'start']
        i = 0
        while coords is None and i<len(options):
            src = options[i]
            if hasattr(self, src) and getattr(self, src) is not None:
                coords = getattr(self, src).value 
            i += 1

        if coords is not None:
            return f'<{self.entity_type} @ {coords}>'
        return f'<{self.entity_type}>'
    
class PolygonWrapper(GraphicalElementWrapper):
    def __repr__(self):
        return f'<{self.entity_type} {len(self.pts)} points>'
    
    
class TextElementWrapper(GraphicalElementWrapper):
    
    def __repr__(self):
        txt = self.value
        if len(txt) > 14:
            txt = f'{txt[:12]}...'
        return f'<{self.entity_type} @ {self.at.value} "{txt}">'
    