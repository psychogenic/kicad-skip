'''
Created on Jan 29, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import sexpdata
import re
import logging 
log = logging.getLogger(__name__)
MaxLineLength = 255*3
def loadTree(fpath:str):
    with open(fpath, 'r') as f:
        return sexpdata.loads(f.read())

def writeTree(fpath:str, tree):
    remove_nones(tree)
    with open(fpath, 'w') as f:
        # no way to pretty print this what the fuck?
        # lines get too long with some schems, when it's all 
        # clumped into a bunch
        as_str = sexpdata.dumps(tree)
        for elname in ['property', 'symbol', 'wire', 'data', 'label', 
                       'global_label', 'text', 'junction', 'polyline', 'rectangle', 'xy']:
            as_str = re.sub(f'\(\s*{elname}', f'\n\n({elname}', as_str)
            
        out_lines = []
        for aline in as_str.split('\n'):
            if len(aline) > MaxLineLength and aline.startswith('(data'):
                aline = re.sub(' ', ' \n', aline)
            out_lines.append(aline)
                
        f.write('\n'.join(out_lines))
    
def list_splice(target, start, delete_count=None, *items):
    """Remove existing elements and/or add new elements to a list.

    target        the target list (will be changed)
    start         index of starting position
    delete_count  number of items to remove (default: len(target) - start)
    *items        items to insert at start index

    Returns a new list of removed items (or an empty list)
    https://gist.github.com/jonbeebe/44a529fcf15d6bda118fe3cfa434edf3
    """
    if delete_count == None:
        delete_count = len(target) - start

    # store removed range in a separate list and replace with *items
    total = start + delete_count
    removed = target[start:total]
    target[start:total] = items

    return removed
    
    
def remove_nones(alist):
    
    targets = []
    for i in range(len(alist)):
        el = alist[i]
        if el is None:
            targets.append(i)
        elif isinstance(el, list):
            remove_nones(el)
            
    if not len(targets):
        #print("No targets here")
        return 
    for killme in sorted(targets, reverse=True):
        #print(f"KILLING {alist[killme]}")
        list_splice(alist, killme, 1)
        
    return
    
