'''
Created on Feb 1, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

import re
from skip.collection import NamedElementCollection
from skip.sexp.parser import ParsedValue, ParsedValueWrapper

import logging 
log = logging.getLogger(__name__)
class LayerCollection(NamedElementCollection):
    '''
       

    '''
    LayerNameCleanerRegex = re.compile(r'[^\w\d_]')
    def __init__(self, parent, elements:list):
        super().__init__(parent, elements, lambda lyr: LayerCollection.LayerNameCleanerRegex.sub('_', lyr.value[0]))
        

class LayerWrapper(ParsedValueWrapper):
    '''
        A layer in the PCB.
        
        Has
          - an id
          - a name
          - and a type
          
        read-only attribs, at least at this stage of dev--anyone need to edit these??
    
    '''
    def __init__(self, v:ParsedValue):
        super().__init__(v)
        self._id = v.raw[0]
        self._name = v.raw[1]
        self._type = v.toString(v.raw[2])
    
    @property 
    def id(self):
        return self._id 
    
    @property 
    def name(self):
        return self._name 
    
    @property 
    def type(self):
        return self._type
    
    def __repr__(self):
        return f'<Layer {self.id} {self.name} ({self.type})>'
        
    
class LayersListWrapper(ParsedValueWrapper):
    '''
        All layers available.
        
        These may be accessed:
          * as attrbutes (names slightly munged for Python's sake):
            layers.Edge_Cuts
            layers.F_Adhes
            layers.F_CrtYd
            layers.F_Cu
            layers.In1_Cu
            layers.In2_Cu
            layers.B_Cu
            
          * by actual name
            >>> layers['B.Cu']
            <Layer 31 B.Cu (signal)>
          
          * by id, same way
            >>> layers[31]
            <Layer 31 B.Cu (signal)>
        
            
        Because the IDs aren't actually sequential, if you want to loop over all layers,
        use the children (won't somebody use the children?!)
        
        for layer in pcb.layers.children:
            # do something
        
        
        These layer instance children also show up in other places, e.g. 
        as the 'layer' attribute of a Segment, so you can do things like:
        
        filter(lambda seg: seg.layer == pcb.layers.In1_Cu, pcb.segment)


    '''
    
    def __init__(self,v:ParsedValue):
        super().__init__(v)
        self._layer_attrib_names = []
        self._layers_by_id = {}
        self._layers_children_list = []
        for i in range(len(v.children)):
            c = LayerWrapper(v[i])
            v.children[i] = c 
            c_clean = v.toSafeAttributeKey(c.name)
            self._layers_by_id[c.id] = c   # 
            self._layers_by_id[c.name] = c # so you can do pcb.layers[segment.layer.value]
            self._layer_attrib_names.append(c_clean)
            setattr(self, c_clean, c)
    
    
    def __contains__(self, key):
        return key in self._layers_by_id
    
    def __getitem__(self, key:int):
        '''
            layers by id
        '''
        if key in self._layers_by_id:
            return self._layers_by_id[key]
        
        
        raise AttributeError(f'No {key} here')
        
        
    def __len__(self):
        return len(self.children)
    
    def __dir__(self):
        return super().__dir__() + self._layer_attrib_names
    
    
    def __repr__(self):
        return f'<Layers ({len(self)})>'
    
    
    
class LayerPropertyHandler:
    def __init__(self, pvLayer:ParsedValue, topLevelParent):
        self._layer_el = pvLayer 
        self._layer_cache = None
        self._top = topLevelParent
        
    def get(self):
        if self._layer_cache is not None:
            return self._layer_cache
        top = self._top 
        if self._layer_el.value in top.layers:
            return top.layers[self._layer_el.value]
        
        log.warn(f"Can't find layer {self._layer_el.value} in layers?")
        return self._layer_el
    
    def set(self, setTo):
        self._layer_cache = None
        top = self._top 
        if hasattr(setTo, 'name') and setTo.name is not None and setTo.name in top.layers:
            self._layer_el.value = setTo.name 
            return 
        
        if isinstance(setTo, str) and setTo in top.layers:
            self._layer_el.value = setTo 
            return 
            
        if isinstance(setTo, int) and setTo in top.layers:
            self._layer_el.value = top.layers[setTo].name
            return
            
        log.error(f"Don't know how to set layer '{setTo}' for footprint?")
        
        return 