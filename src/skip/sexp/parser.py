'''
Created on Jan 29, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

import sexpdata
import uuid
import re
import copy

import logging 
log = logging.getLogger(__name__)
class AccessesTree:
    def __init__(self, sourceTree):
        self._sourceTree = sourceTree
        
    @property
    def sourceTree(self):
        return self._sourceTree
    
        
    
    def _setOnTree(self, coordsList, val):
        c = self.sourceTree 
        for i in range(len(coordsList) - 1):
            c = c[coordsList[i]]
            
        c[coordsList[-1]] = val 
        
    def _deleteOnTree(self, coordsList):
        c = self.sourceTree 
        for i in range(len(coordsList) - 1):
            c = c[coordsList[i]]
            if c is None:
                return 
        
        if c[coordsList[-1]] is None:
            return 
        c[coordsList[-1]] = None 



class ParsedValue(AccessesTree):
    '''
        The result of parsing a basic sexpdata value.
        
        It is augmented in many ways to allow for actual sane usage.
        
        Short version is will parse simple expressions, like
        [Symbol('lib_id'), 'Device:C_Small']
        so they have a 'value'
            lib_id.value == 'Device:C_Small'
        which may be used to overwrite the value
            lib_id.value = 'lalala'
        
        More complex objects may have children, a list of elements also ParsedValue
        recursively
        E.g. 
         [Symbol('instances'), 
            [Symbol('project'), 
               'tinytapeout-demo', 
                 [Symbol('path'), '/20adca1d-43a1-4784-9682-8b7dd1c7d330', 
                 [Symbol('reference'), 'C4'], [Symbol('unit'), 1]]]]
        would have such that
         instances.children[0].value == 'tinytapeout'
         instances.children[0].children[2].value == 'C4'
         
        Children are also accessible as attributes.  
        If a there are (possibly) many children of the same type, this attribute will
        be list-like:
         instances.project[0].path.reference.value == 'C4'
         
        otherwise they are just objects.  Finally, some children that would be 
        simple lists are replaced by specialized collections in higher levels 
        to allow for things like named-access
        
          schematic.symbol.C4.property.Description.value
         
        rather than only having
        
          schematic.symbol[idx].property[3].value
        
        though that will still work.
        
        
        This class is pretty generic and agnostic about the contents of the
        sexpressions except that it knows about 'at' (an element with a list
        of coordinates and rotation), and will automagically provide
            move() and
            translation() 
        methods on elements that have these as children.
        
        @note: when you have a parsed value in a REPL use tab completion 
        to discover what's available to you: schematic.symbol.<TAB><TAB> is
        very nice.
        
    '''
    AttribInvalidCharsRe = re.compile(r'[^\w\d\_]')
    StrStartsWithDigitRe = re.compile(r'^\d')
    PositionPrecision = 6
    @classmethod 
    def toString(cls, val):
        if isinstance(val, sexpdata.Symbol):
            return str(val.value())
        return str(val)
    
    @classmethod 
    def toSafeAttributeKey(cls, val:str):
        val = cls.AttribInvalidCharsRe.sub('_', val)
        if cls.StrStartsWithDigitRe.match(val):
            val = f'n{val}'
        return val
       
    def __init__(self, sourceTree, tree, base_coords, parent=None):
        '''
            ParsedValue c'tor
            
            @param sourceTree: the whole guacamole
            @param tree: the value we're parsing
            @param base_coords: the path, in sourceTree, to get here
            @param parent: the parent ParsedValue    
        
        '''
        super().__init__(sourceTree)
        self._parent_obj = parent
        self._parent_top_obj = None
        self._entity_name = None 
        self._base_coords = base_coords 
        self._deleted = False
        self._tree = tree 
        self._value = None
        self.children = []
        
        self._added_children_names = []
        
        self._parseTree(tree)
        
        if hasattr(self, 'at'):
            self.move = self._move_method
            self.translation = self._translate_method # translate was taken
        
        
                     
    @property 
    def value(self):
        '''
            the "value" tries to be the thing represented 
            by this entry    
        
        '''
        if self._value is None and len(self.children):
            return self.children 
            
        as_bool = self._as_boolean(self._value) 
        if as_bool is not None:
            return as_bool 
        
        if isinstance(self._value, sexpdata.Symbol):
            return self._value.value()
        return self._value 
        
    @value.setter 
    def value(self, setTo):
        '''
            Set values on the .value attribute.
            
            E.g. 
            sch.symbol.C4.dnp.value = True 
        
        '''
        if self._is_bool_symbol(self._value):
            
            if not isinstance(setTo, str):
                
                if setTo:
                    if self._is_yesno_bool(self._value):
                        setTo = 'yes'
                    else:
                        setTo = 'true'
                else:
                    if self._is_yesno_bool(self._value):
                        setTo = 'no'
                    else:
                        setTo = 'false'
            self._value = sexpdata.Symbol(setTo)
        else:
            if isinstance(self._value, sexpdata.Symbol):
                self._value = sexpdata.Symbol(setTo)
            else:
                self._value = setTo
            
        if self.sourceTree is not None and len(self.sourceTree) >= self._base_coords[0]:
            c = self.sourceTree
            for i in range(len(self._base_coords)):
                c = c[self._base_coords[i]]
                
            if isinstance(c, list) and len(c) > 1:
                if isinstance(self._value, list):
                    c[1:] = self._value 
                    #print(f"Setting values as list on {c}")
                else:
                    c[1] = self._value
                    #print(f"Setting values as list on idx 1 of {c}")
                    
                if len(self.children) and type(setTo) == type(self.children[0]):
                    self.children[0] = self._value
            else:
                print(c)
                raise KeyError(f'dunno how to handle setting {c}')
   
    def clone(self):
        '''
            Constructing something complex like a component ("symbol"), 
            or even a property would be a major pain.
            
            Instead, find something you like and clone it.
            
              newCap = sch.symbol.C4.clone()
            This is a deep copy, that is inserted in the tree at the same
            level.
            
            So 
              newProp = sch.symbol.R10.property.Description.clone()
              
            Creates a new property *on* symbol "R10"
            
        '''
        rawclone = copy.deepcopy(self.raw)
        rawpar = self.raw_parent
        idx = len(rawpar)
        rawpar.append(rawclone)
        
        coords = copy.deepcopy(self._base_coords)
        coords[-1] = idx 
        clonedObj = ParsedValue(self.sourceTree, rawclone, coords, self.parent)
        for a_uuid in clonedObj.getElementsByEntityType('uuid'):
            a_uuid.value = str(uuid.uuid4())
        
        wrappedClone = clonedObj
        if clonedObj.parent_top is not None:
            wrappedClone = clonedObj.parent_top.wrap(clonedObj)
        
        if self.parent is not None:
            log.debug(f'Have parent of type{type(self.parent)}')
            if hasattr(self.parent, 'children'):
                log.debug(f'adding to children')
                self.parent.children.append(clonedObj)
            else:
                # log.error(f'no chiiiwdwen children')
                log.info(f'Object parent exists but has no children {self.parent}')
                if hasattr(self.parent, self.entity_type):
                    ent_container = getattr(self.parent, self.entity_type)
                    if hasattr(ent_container, 'append'):
                        ent_container.append(wrappedClone)
                        
                        
        
        return wrappedClone
        
        
        
    def delete(self):
        
        self._deleted = True
        
        self._deleteOnTree(self._base_coords)
        
        for c in self.children:
            if hasattr(c, 'delete'):
                c.delete()
                
    @property 
    def entity_type(self):
        return self._entity_name
    
    @property 
    def parent(self):
        return self._parent_obj
    
    @property 
    def parent_top(self):
        if self._parent_top_obj is not None:
            return self._parent_top_obj
        
        p = self.parent
        if p is None:
            return None 
        
        while hasattr(p, 'parent') and p.parent is not None:
            p = p.parent 
        
        self._parent_top_obj = p 
        
        return p
        
        
        
                
        
    def getElementsByEntityType(self, tp:str):
        return self._crawlForElementsByType(tp, self.children)
        
    @property 
    def raw(self):
        c = self.sourceTree 
        for coord in self._base_coords:
            c = c[coord]
            
        return c
    
    
    @property 
    def raw_parent(self):
        c = self.sourceTree 
        for i in range(len(self._base_coords) - 1):
            c = c[self._base_coords[i]] 
            
        return c 
    
    
    
    def _move_method(self, xcoord:float, ycoord:float=None, rotation:int=None):
        '''
            update this element's "at" value to place it at xcoord, ycoord.
            Rotation param may be passed to set rotation, this must be 
            an int of 0,90,180 or 270
            
            @param xcoord: x-coordinate float, or xy list/tuple (so you can use .at.value)
            @param ycoord: y-coordinate float, required if xcoord isn't a list/tuple
            @param rotation: required int if you wish to affect rotation
        '''
        rot = None
        
        if isinstance(xcoord, ParsedValue) and isinstance(xcoord.value, (list)):
            xcoord = xcoord.value
            
        if isinstance(xcoord, (list, tuple)) and len(xcoord) > 1:
            clist = xcoord 
            xcoord = clist[0]
            ycoord = clist[1]
        
        if len(self.at.value) > 2:
            rot = self.at.value[2]
            if rotation is not None:
                rot = rotation 
            
        
        deltax = xcoord - self.at.value[0]
        deltay = ycoord - self.at.value[1]
        
        # don't call this:
        # self.at.value = [xcoord, ycoord, rot]
        # want to recurse with translate
        self._translate_method(deltax, deltay, rot)
        
        
        
    def _translate_method(self, by_x:float, by_y:float, set_rot:int=None):
        new_loc = [ 
                round(self.at.value[0] + by_x, self.PositionPrecision), 
                round(self.at.value[1] + by_y, self.PositionPrecision)
                ]
        
        if len(self.at.value) > 2:
            if set_rot is None:
                set_rot = self.at.value[2]
            
            new_loc.append(set_rot)
        
        self.at.value = new_loc
        for child in self.children:
            if hasattr(child, 'translation'):
                child.translation(by_x, by_y)
         
    def _parseTree(self, tree):
        if not isinstance(tree, list):
            self._value = tree 
            return 
            
        coord_adjust = 0
        
            
        if len(tree):
            
            self._entity_name = self.toString(tree[0])
            log.debug(f'GOT NAME {self._entity_name} from first element')
            coord_adjust = 1
            tree = tree[1:]
            
        if len(tree) == 1:
            log.debug(f'Len of tree is 1 {tree}, done here')
            if isinstance(tree[0], list):
                if len(tree[0]) and not isinstance(tree[0][0], sexpdata.Symbol):
                    self._value = tree[0]
            else:
                self._value = tree[0]
                
            if self._value is not None:
                return 
            
        
        children = []
        childnameCounts = {}
        all_entries_simple = True
        for (idx, entry) in enumerate(tree):
            child_coord = []
            for i in self._base_coords:
                child_coord.append(i) 
            child_coord.append(idx + coord_adjust)
            log.debug(f'Parse subentry {entry}')
            if isinstance(entry, list) and len(entry):
                entry_name = self.toSafeAttributeKey(self.toString(entry[0]))
                if entry_name not in childnameCounts:
                    childnameCounts[entry_name] = 1
                else:
                    childnameCounts[entry_name] += 1
                parsed = ParsedValue(self.sourceTree, entry, child_coord, self)
                
                log.debug(f"Appended entry at {child_coord}: {parsed}")
                children.append(parsed)
                all_entries_simple = False
            else:
                children.append(entry)
        
        self.children = children
        self._nameCounts = childnameCounts # just keeping for debug
        specialChildrenCollections = {}
        
        if all_entries_simple:
            self._value = children
        else:
            for c in children:
                if not isinstance(c, ParsedValue):
                    if self._value is None:
                        self._value = c
                    elif not isinstance(self._value, list):
                        self._value = [self._value, c]
                    else:
                        self._value.append(c)
                    continue
                    
                centry_name = self.toSafeAttributeKey(c.entity_type)
                if centry_name in childnameCounts and childnameCounts[centry_name] > 1:
                    
                    if centry_name in specialChildrenCollections:
                        if not hasattr(self, centry_name):
                            ccont = specialChildrenCollections[centry_name](self.sourceTree, centry_name)
                            setattr(self, centry_name, ccont)
                            self._added_children_names.append(centry_name)
                        ccont = getattr(self, centry_name)
                        ccont.append(c) 
                    else:
                        pluralentry_name = f'{centry_name}' # actually leaving same now
                        if not hasattr(self, pluralentry_name):
                            setattr(self, pluralentry_name, [])
                            self._added_children_names.append(pluralentry_name)
                        
                        v = getattr(self, pluralentry_name) 
                        v.append(c) 
                else:
                    if hasattr(self, centry_name):
                        log.warn(f"OVERWRITING {centry_name}")
                    else:
                        self._added_children_names.append(centry_name)
                    setattr(self, centry_name, c)
      
    
    
    
    
    
    
    
    def _crawlForElementsByType(self, tp:str, elements:list):
        retVal = []
        for el in elements:
            if isinstance(el, ParsedValue):
                if el.entity_type == tp:
                    retVal.append(el)
                retVal.extend(el.getElementsByEntityType(tp))
            elif isinstance(el, list):
                retVal.extend(self._crawlForElementsByType(tp, el))
        
        return retVal
            
            
    def __bool__(self):
        if self._is_bool_symbol(self._value):
            return self._as_boolean(self._value)
        return self._value
    def _is_bool_symbol(self, v):
        if not isinstance(self._value, sexpdata.Symbol):
            return False 
            
        val = v.value()
        
        validBooleans = ['yes', 'no', 'true', 'false']
        
        return val in validBooleans
    
    def _is_yesno_bool(self, v):
        if not isinstance(self._value, sexpdata.Symbol):
            return False 
            
        val = v.value()
        return val in ['yes', 'no']
        
        
        
    def _as_boolean(self, v):
        if not self._is_bool_symbol(v):
            return None
        
        vstr = v.value()
        if vstr == 'yes' or vstr == 'true':
            return True
        
        return False
               
            
    def __len__(self):
        return len(self.children)
        
    def __getitem__(self, idx:int):
        return self.children[idx]
    
    def __str__(self):
        bstring = self.__repr__()
        if len(bstring) > 24:
            bstring = f'{bstring[:24]}...'
            
        childrens = []
        for cname in self._added_children_names:
            c = getattr(self, cname)
            childrens.append(str(c))
            
        tabs = "  "*len(self._base_coords)
        nl = f"\n{tabs}"
        return f"{tabs}{bstring}\n{nl.join(childrens)}"
            
        
        
    def __repr__(self):
        if len(self.children) < 2:
            return f'{self.entity_type} = {self.toString(self.value)}' 
        
        v = self.value 
        
        if hasattr(self, 'property') and hasattr(self.property, 'Reference'):
            v = self.property.Reference.value 
        else:
            if v is None:
                v = ''
            elif isinstance(v, list):
                if len(v) > 3:
                    v = f'[{v[0]}, {v[1]}, ...]'
            elif isinstance(v, str):
                if len(v) > 10:
                    v = f"'{v[:10]}...'"
        return f'<{self.entity_type} {v}>' # , {len(self.children)} children {str(self.children)}>'


class ParsedValueWrapper:
    '''
        It's job is just to wrap a ParsedValue and pass
        along requests to the underlying object.  That 
        sure seems useless, but is a way for the parser
        to return a bunch of ParsedValue objects, and 
        for higher levels to extend this class and 
        wrap things as they please.
    '''
    def __init__(self,v:ParsedValue):
        self._pv = v
        

    def __contains__(self, name:str):
        return hasattr(self._pv, name)
    
    def __getattr__(self, name:str):
        if not hasattr(self._pv, name):
            #raise AttributeError(f"no '{name}' in {self._pv}")
            log.debug(f'no "{name}" found')
            return None
        return getattr(self._pv, name)
    
    def __dir__(self):
        return dir(self._pv)
    
    def __str__(self):
        return str(self._pv)
    
    
    @property 
    def value(self): 
        return self._pv.value 
    
    @value.setter
    def value(self, x):
        self._pv.value = x
    
    
    def getValue(self):
        return self._pv.value 
    def setValue(self, x):
        self._pv.value = x
    
    @property 
    def wrapped_parsed_value(self):
        return self._pv
    
class ArbitraryNamedParsedValueWrapper(ParsedValueWrapper):
    def __init__(self, pv:ParsedValue):
        super().__init__(pv)
        
        coords = []
        for i in pv._base_coords:
            coords.append(i)                        
        #coords.append(2)
        self._name_coords = copy.deepcopy(coords)
        self._val_coords = coords
        self._name_coords.append(1)
        self._val_coords.append(2)
        
        name = self._cleanse_name(pv.toString(pv.children[0]))
        self._name = name
    
    def _cleanse_name(self, nm:str):
        return re.sub(r'[^\w\d_]', '_', nm)
    @property 
    def name(self):
        '''
            the name of this nameable element... stuff like symbol properties, 
            i.e. the Reference and Datasheet in the part details, can be 
            augmented with user-named element, say "MPN"
            
            This provides a way to get and set that name (thereby influencing 
            the containing elements available attributes)
            
            @see: property.PropertyString for contrete examples
        '''
        return self._name 
    
    @name.setter 
    def name(self, setTo:str):
        oldName = self._name
        self.children[0] = setTo
        name = self._cleanse_name(setTo)
        self._setOnTree(self._name_coords, setTo)
        self.updateParentCollection(oldName, name)
        self._name = name
    @property 
    def value(self): 
        '''
            the value of this nameable element... stuff like symbol properties, 
            i.e. the Reference and Datasheet in the part details, have a definite 
            value, as well as other children.
            @see: property.PropertyString for contrete examples
        '''
        return self.getValue()
    
    @value.setter
    def value(self, x):
        self.setValue(x)
    
    def getValue(self):
        return self.children[1] 
    def setValue(self, x):
        self.children[1] = x
        self._setOnTree(self._val_coords, x)
    
    
    def updateParentCollection(self, oldName:str, newName:str):
        pass 
    
    def __repr__(self):
        return f"<NamedValue {self.name} = '{self.value}'>"
    
        
    def __str__(self):
        tabs = "  "*len(self._base_coords)
        return f'{tabs}{self.name}:\n{str(self._pv)}'
    
    