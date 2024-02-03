'''
Created on Jan 30, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from skip.eeschema.schematic import Schematic, Symbol

def get_schematic(filepath:str) -> Schematic:
    '''
        Just load a Schematic object, from file
    '''
    return Schematic(filepath)

def translate_all_resistors(sch:Schematic, by_x:float=10, by_y:float=10):
    '''
        Move all matching components by a given delta
    
    '''
    for r in sch.symbol.reference_startswith('R'):
        r.translation(by_x, by_y)
        


def copy_and_move_all_resistors(sch:Schematic, by_x:float=250, by_y:float=0):
    '''
        Will create exact duplicates of all resistors, then shift them by x,y
        (far to the right by default)
    '''
    for r in sch.symbol.reference_startswith('R'):
        acopy = r.clone()
        acopy.translation(by_x, by_y)


def dnp_parts(parts_list):
    '''
        Set parts in list as DNP 
    '''
    for c in parts_list:
        c.dnp.value = True 
        
def dnp_parts_matching(sch:Schematic, referenceRegex:str):
    '''
        DNP all parts who's reference matches the regex
    '''
    dnp_parts(sch.symbol.reference_matches(referenceRegex))
    
def dump_properties(sym:Symbol):
    '''
        Pretty print out a symbol (component's) properties
    '''
    print(f"\n\nProperties for symbol {sym.property.Reference.value}/{sym.property.Value.value}")
    for prop in sym.property:
        print(f'  {prop.name} = {prop.value}')

def dump_standard_attribs(sym:Symbol):
    print(sym.dnp)
    print(sym.in_bom)
    print(sym.on_board)
    print(sym.exclude_from_sim)
    
    
def dump_symbol(sym:Symbol):
    dump_properties(sym)
    dump_standard_attribs(sym)
        
def dump_mpn(sym:Symbol):
    '''
        Print out the custom 'MPN' property, if available, for this component.
        
    '''
    if 'MPN' in sym.property:
        print(f'MPN is {sym.property.MPN.value}')
    else:
        print("MPN not set")
    
def find_symbols_without_mpn(sch:Schematic, do_output:bool = False):
    '''
        return a list of all symbols with no "MPN" property, or 
        one that is empty
    '''
    unset_mpn_symbols = []
    for s in sch.symbol:
        if 'MPN' in s.property and len(s.property.MPN.value):
            if do_output:
                print(f'{s.property.Reference.value} has MPN: {s.property.MPN.value}')
        else:
            # I don't want all the power symbols here
            if not s.is_power: # same as s.lib_id.value.startswith('power:'):
                unset_mpn_symbols.append(s)
            
    return sorted(unset_mpn_symbols)

def find_symbols_with_mpn_set_to(sch:Schematic, set_to_value):
    ''' 
        filter out based on MPN
    '''
    return sorted(list(filter(lambda s: 'MPN' in s.property and s.property.MPN.value == set_to_value,
                              sch.symbol)))

def show_symbols_without_mpn(sch:Schematic):
    '''
        Dump all symbols with no or empty "MPN" property
    '''
        
    unsets = find_symbols_without_mpn(sch, do_output=True)
    
    if not len(unsets):
        print("All components have MPN!")
    else:
        print("\n\nComponents without MPN set")
        for s in unsets:
            more_info = ''
            if 'MPN' not in s.property:
                more_info = 'no MPN property'
            else:
                more_info = 'empty MPN'
            print(s.property.Reference.value, more_info)
        

def add_mpn_to_all_symbols(sch:Schematic, default_value:str='N/A'):
    '''
        Add an MPN property, if not set or empty, and set it to default_value.
    '''
    unsets = find_symbols_without_mpn(sch)
    count = 0
    for sym in unsets:
        if 'MPN' not in sym.property:
            mpn = sym.property.Reference.clone()
            mpn.name = 'MPN'
            mpn.value = default_value 
        else:
            sym.property.MPN.value = default_value
        count += 1
        
    return count 

def find_all_movable_children(sym:Symbol, highlevel:bool=True):
    if highlevel:
        # just find every child that can be move()d
        return list(filter(lambda c: hasattr(c, 'move'), sym.children))
    else:
        # this is some under the hood stuff
        # move/translation enabled elements have an 'at' child somewhere 
        # within
        # so we get all the 'at' elements and then return their parent
        return list(map(lambda element: element.parent, sym.getElementsByEntityType('at')))
        

def update_component_value(sym:Symbol, toValue:str):
    
    sym.property.Value.value = toValue # yeah, that's ugly I know
    
def update_all_1k_Rs(sch:Schematic, toValue:str='11k'):
    for r in sch.symbol.value_matches(r'1k'):
        if r.property.Reference.value.startswith('R'):
            r.property.Value.value = toValue
            
    
if __name__ == '__main__':
    fpath = input('Enter path to a schematic (no worries will NOT overwrite): ')
    if not len(fpath):
        print("Aborted")
    else:
        sch = get_schematic(fpath)
        
        print(f"Properties for a few components  ({len(sch.symbol)} total)")
        for i in range(len(sch.symbol)):
            if i > 6 or sch.symbol[i].is_power:
                continue 
            dump_symbol(sch.symbol[i])
            
        
        print("\n\n")
        if 'R1' in sch.symbol:
            print(f"Found component R1 and it's at {sch.symbol.R1.at.value}")
        
        print("Adding MPN 'MYMPN' to all parts that don't have it set")
        add_mpn_to_all_symbols(sch, 'MYMPN')
        
        print("DNPing all Caps -- no decoupling for you")
        dnp_parts_matching(sch, 'C.*')
        print("No sim either")
        for s in sch.symbol:
            if s.dnp.value:
                if 'exclude_from_sim' in s:
                    s.exclude_from_sim.value = True 
                else:
                    print(f"symbol {s.property.Reference.value} does not have an 'exclude_from_sim' prop")
        
        
        print("Changing all 10k Rs to 13k333")
        update_all_1k_Rs(sch, '13k333')
        
        
        input("\n\n================\nHit enter to see those first few comps after mods")
        for i in range(len(sch.symbol)):
            if i > 6 or sch.symbol[i].is_power:
                continue 
            dump_symbol(sch.symbol[i])
        
        print("Making a copy of all resistors, and moving it to the right")
        copy_and_move_all_resistors(sch)
        
        savepath = input('Path to save results? WILL WRITE TO THIS FILE (empty to skip): ')
        if len(savepath):
            sch.write(savepath)
        