'''
Created on Feb 2, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import math
from skip.collection import ElementCollection
from skip.sexp.parser import ParsedValue, ParsedValueWrapper
from skip.element_template import ElementTemplate
# from skip.at_location import AtValue

class WireWrapper(ParsedValueWrapper):
    RoundPrecision = 4
    def __init__(self,v:ParsedValue):
        super().__init__(v)
        self._slope = None 
        self._unit_vector = None 
        self._wire_mag = None
        self._specs_calculated = False
        
    def translation(self, by_x:float, by_y:float):
        self._unit_vector = None 
        self._slope = None 
        for p in self.points:
            p.value = [round(p.value[0] + by_x, 6), round(p.value[1] + by_y, 6)]
    
    
    
    @property 
    def points(self):
        return self.pts.xy
    
    def _to_coords_list(self, coords):
        if isinstance(coords, list):
            return coords 
        
        if hasattr(coords, 'at') and coords.at is not None:
            return coords.at.value 
        
        if hasattr(coords, 'location') and coords.location is not None:
            return coords.location.value
        
        if hasattr(coords, 'value') and isinstance(coords.value, list):
            return coords.value
        
        
        raise ValueError(f"Don't know how to get coordinates from {coords}")
        
    def start_at(self, coords):
        coords = self._to_coords_list(coords)
        self.start.value = [round(coords[0], self.RoundPrecision), round(coords[1], self.RoundPrecision)]
    
    @property 
    def start(self):
        self._specs_calculated = False
        return self.pts.xy[0]
    
    def end_at(self, coords):
        coords = self._to_coords_list(coords)
        self.end.value = [round(coords[0], self.RoundPrecision), round(coords[1], self.RoundPrecision)]
        
    @property 
    def delta_x(self):
        return round(self.end.value[0] - self.start.value[0], self.RoundPrecision)
    
    @delta_x.setter 
    def delta_x(self, delta:float):
        self.pts.xy[1].value =  [round(self.start.value[0] + delta, self.RoundPrecision), self.end.value[1]]
        
        
    @property 
    def delta_y(self):
        return round(self.end.value[1] - self.start.value[1], self.RoundPrecision)
        
        
    @delta_y.setter 
    def delta_y(self, delta:float):
        self._wire_mag = None # reset 
        self.pts.xy[1].value = [self.end.value[0], round(self.start.value[1] + delta, self.RoundPrecision)]
        
    @property 
    def end(self):
        self._specs_calculated = False
        return self.pts.xy[1]
    
    @property 
    def length(self):
        if not self._specs_calculated:
            self._calculate_specs()
        
        return round(self._wire_mag, 4)
    
    def list_connected_symbols(self, recursive_crawl:bool = False):
        all_syms = set()
        if recursive_crawl:
            all_wires = self.crawl_connected_wires()
            for w in all_wires:
                for sym in w.list_connected_symbols(False):
                    all_syms.add(sym)
        else:
            startpoint = self.start.value 
            endpoint = self.end.value 
            for sym in self.parent.symbol:
                if sym is None or 'pin' not in sym:
                    continue
                addIt = None 
                for pin in sym.pin:
                    if addIt is not None:
                        continue 
                    try:
                        pinloc = pin.location 
                    except:
                        continue
                    if pinloc.x == startpoint[0] and pinloc.y == startpoint[1]:
                        addIt = sym 
                    elif pinloc.x == endpoint[0] and pinloc.y == endpoint[1]:
                        addIt = sym 
                
                if addIt is not None:
                    all_syms.add(addIt)
            
        return list(all_syms)
                        
                        
                    
                
    
    def list_labels(self, recursive_crawl:bool=False):
        all_labels = set()
        if recursive_crawl:
            all_wires = self.crawl_connected_wires()
            for w in all_wires:
                for lbl in w.list_labels(False):
                    all_labels.add(lbl)
        else:
            for p in self.list_points(1):
                lbls = self.parent.label.within_circle(p[0], p[1], 0.6)
                for lb in lbls:
                    all_labels.add(lb)
        
        return list(all_labels)
    
    
    def list_global_labels(self, recursive_crawl:bool=False):
        all_labels = set()
        
        if recursive_crawl:
            all_wires = self.crawl_connected_wires()
            for w in all_wires:
                for lbl in w.list_global_labels(False):
                    all_labels.add(lbl)
        else:
            for p in self.list_points(1):
                lbls = self.parent.global_label.within_circle(p[0], p[1], 0.6)
                for lb in lbls:
                    all_labels.add(lb)
        
        return list(all_labels)
    
    def crawl_connected_wires(self, into_list:set = None):
        
        if into_list is None:
            into_list = set()
        for p in [self.start, self.end]:
            found_wires = self.parent.wire.all_at(p[0], p[1])
            for w in found_wires:
                if w != self and w not in into_list:
                    w.crawl_connected_wires(into_list)
                into_list.add(w)
                        
                        
        return list(into_list)
            
    
    def list_points(self, step:float=1):
        uv = self.unit_vector
        max_len = self.length
        start_point = self.start.value
        
        if step <= 0:
            raise ValueError('Step must be positive')
        
        points_list = []
        cur_len = 0
        while cur_len < max_len:
            cur_point = [ round((start_point[0] + (uv[0]*cur_len)), 5), 
                          round((start_point[1] + (uv[1]*cur_len)), 5)]
            points_list.append(cur_point)
            
            cur_len += step
            
        points_list.append(self.end.value)
        
        return points_list
    
    @property 
    def unit_vector(self):
        if self._specs_calculated:
            return self._unit_vector
        self._calculate_specs()
        return self._unit_vector
        
    
    def _calculate_specs(self):
        start_x = self.start.value[0]
        start_y = self.start.value[1]
        
        end_x = self.end.value[0]
        end_y = self.end.value[1]
        
        dx = end_x - start_x
        dy = end_y - start_y 
        
        wire_mag = math.sqrt( (dx*dx) + (dy*dy))
        
        if dx == 0:
            slope = 1e9
            vect_mag = dy
            self._unit_vector = (0, 1.0)
        else:
            slope = dy/dx
            vect_mag = math.sqrt(  (1) + (slope**2))
            normalizer = 1/vect_mag
            self._unit_vector = (normalizer, slope/normalizer) 
        
        self._specs_calculated = True
        self._wire_mag = wire_mag
        self._slope = slope
        
        
    def __repr__(self):
        start = self.start.value 
        end = self.end.value 
        return f'<Wire {start} - {end}>'
        

class WireCollection(ElementCollection):
    def __init__(self, parent, elements:list):
        super().__init__(parent, elements)
        
    def all_at(self, x:float, y:float):
        ret_val = []
        for w in self:
            for p in w.points:
                #print(f"CHECK {p.value} for {x},{y}")
                if p.value[0] == x and p.value[1] == y:
                    ret_val.append(w)
        
        return ret_val
    
    
    def within_circle(self, xcoord:float, ycoord:float, radius:float):
        '''    
            Find all elements of this collection that are within the 
            circle of radius radius, centered on xcoord, ycoord.
            
            @note: only works for elements that have a
            suitable 'at' or 'location' attribute
        
        '''
        retvals = []
        if not len(self._elements):
            return retvals
        
        
        target_coords = [xcoord, ycoord]
        for el in self:
            append = False
            for p in el.points:
                if self._distance_between(target_coords, p.value) <= radius:
                    append = True
                    
            if append:
                retvals.append(el)
            
        return retvals
        
    
    def _new_instance(self):
        newObj = WireWrapper(self.parent.new_from_list(ElementTemplate['wire']))
        return newObj
        
    def __repr__(self):
        return f'<WireCollection ({len(self)} wires)>'