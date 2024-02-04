'''
Created on Feb 1, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
'''
Main handle to kicad schematic.

This is the top level object for all the action in this library.  If you


import skip
sch = skip.Schematic('path/to/file.kicad_sch')


then sch will hold a number of attributes, which depend on the contents
of the schematic.


*DO* use a console and TAB-completion to explore the object.

sch.<TAB><TAB>  will show a number of members.  
Some of most interest are likely


  sch.symbol
  sch.title_block
  sch.text

but you'll also probably find

sch.wire
sch.label
sch.junction
sch.rectangle
and more.

Each attribute will either be:
  * an object 
  * a basic list of objects
  * a collection of objects

Dedicated collections are used in some instances.  These can act just like lists

for component in sch.symbol:
    print(f'Setting datasheet and DNP on {component.property.Reference.value}')
    component.property.Datasheet.value = 'Ho.pdf'
    component.dnp = True

But often also as objects with attributes. For symbols (components) these are the
reference of the component, which is very useful when operating in a console.

Use tab-completion to see them all

sch.symbol.<TAB><TAB>

and use 'em.
sch.symbol.C42.dnp = True


Created on Jan 29, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from skip.sexp.util import loadTree, writeTree
from skip.sexp.parser import ParsedValue
from skip.collection import ElementCollection
import logging 
log = logging.getLogger(__name__)

class SourceFile:
    def __init__(self, filepath:str):
        '''
            c'tor for the sexprdata sourced objects, 
            baseclass for specifically oriented file types (e.g. kicad_sch 
            schematics).
            
            @param filepath: path/to/source.blah
            
            @note: No checking is done at all.  If the file DNE, it dies.  
            If it's not a the kind of file we expect... who knows.
        '''
        self.tree = None
        self._added_attribs = []
        self._dedicatedWrappers = dict()
        self.read(filepath)
        
    @property 
    def filepath(self):
        return self._filepath
        
    def will_load(self, filepath:str):
        '''
            Called prior to a read.
            For overriding in subclasses.
            Return False to abort
        '''
        log.debug(f'Will read {filepath}')
        return True
    
    def will_write(self, filepath:str):
        '''
            Called prior to a write.
            For overriding in subclasses.
            Return False to abort
        '''
        log.debug(f'Will write {filepath}')
        return True
    def dedicated_collection_type_for(self, entity_type:str):
        '''
            For subclass override, called when multiple 
            entities of this type are found, they will be grouped
            in a new collection of this type, if anything other than
            None returned.
            
            @return: Collection type or None
        '''
        log.debug(f"dedicated_collection_type_for {entity_type}")
        
        return None 
    def dedicated_wrapper_type_for(self, entity_type:str):
        '''
            For subclass override, called for entities, to allow 
            wrapping in some class.
            
            @return: ParsedValue wrapper or None
        '''
        log.debug(f"dedicated_wrapper_type_for {entity_type}")
        
        return None 
    
    def read(self, filepath:str):
        '''
            Read in a kicad_sch file.
            @param filepath: path/to/schematic.kicad_sch
        '''
        
        if not self.will_load(filepath):
            log.info(f'Aborting read of {filepath}')
            return
    
        self._filepath = filepath    
        self.tree = loadTree(filepath)
        
        if len(self._added_attribs):
            # we've generated attribs, this is a reload/fresh load
            # get rid of old stuff hanging around
            for aname in self._added_attribs:
                delattr(self, aname)
        
        # clear out the list
        self._added_attribs = []
            
        bytype = {}
        for i, level in enumerate(self.tree):
            try:
                pv = ParsedValue(self.tree, level, [i], self)
                if pv.entity_type not in bytype:
                    bytype[pv.entity_type] = []
                
                bytype[pv.entity_type].append(pv)
            except Exception as e:
                print(f"Problem parsing entry {i}:\n{level}")
                print(e)
        
        self._all = bytype
                
        
        for ent_type,v in bytype.items():
            
            if ent_type is None:
                continue 
            
            # no matter what, we'll have and attrib called this
            self._added_attribs.append(ent_type)
            
            if ent_type not in self._dedicatedWrappers:
                # never seen this type, check for dedicated wrapper
                self._dedicatedWrappers[ent_type] = self.dedicated_wrapper_type_for(ent_type)
            
            # if we have a wrapper for this type
            # wrap all the entities with it and replace  
            entities = []   
            if self._dedicatedWrappers[ent_type] is None:
                # no wrappers, just the same ol' list as-is
                entities = v 
            else:
                wrapClass = self._dedicatedWrappers[ent_type]
                if len(v):
                    entities = list(map(lambda baseobj: wrapClass(baseobj), v))
            
            # this can lead to surprises (eg sheet, which may be single or multiple) 
            # but makes life simpler in most cases
            if len(entities) == 1: 
                setattr(self, ent_type, entities[0]) 
            elif len(entities) > 1:
                # multiple entities, may want a special collection
                dedicatedCollection = self.dedicated_collection_type_for(ent_type)
                
                if dedicatedCollection is None:
                    # nope, just have a list
                    log.debug(f'No deditaced collection for {ent_type}, using default for {len(entities)}')
                    setattr(self, ent_type, ElementCollection(entities))
                else:
                    # yep, stick a collection there
                    log.debug(f'Have a dedicated collection {dedicatedCollection} for {ent_type}--sending {len(entities)} over')
                    setattr(self, ent_type, dedicatedCollection(entities))
    
    def write(self, fpath:str):
        '''
            Write current schematic tree to file.
            @param fpath: path/to/output.kicad_sch
            
            @note: writes the file you specify no checks or hand-holding 
        '''
        if not self.will_write(fpath):
            log.info(f"Write to '{fpath}' aborted")
            return
        writeTree(fpath, self.tree)
        log.info(f"Wrote tree to {fpath}")
        
    
    def reload(self):
        '''
            reloads originally loaded file
        '''
        log.info(f"Reloading '{self._filepath}'")
        self.read(self._filepath)
        
    def overwrite(self):
        '''
            overwrites originally loaded file
        '''
        log.info(f"Overwriting loaded file '{self._filepath}'")
        self.write(self._filepath)   
        
    def wrap(self, pv:ParsedValue):
        ent_type = pv.entity_type
        if ent_type not in self._dedicatedWrappers:
            self._dedicatedWrappers[ent_type] = self.dedicated_wrapper_type_for(ent_type)
        
        wrapped = pv
        if self._dedicatedWrappers[ent_type] is not None:
            wrapClass = self._dedicatedWrappers[ent_type]
            wrapped = wrapClass(pv)
            
        return wrapped


        
    
    def __repr__(self):
        return f"<SourceFile '{self.filepath}'>"

