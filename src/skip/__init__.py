'''
Library to parse and manipulate Kicad 7+ (skip) kicad_sch/kicad_pcb schematic and layout files.

Example usage: Simply create a schematic object by loading a file

import skip
sch = skip.Schematic('/path/to/file.kicad_sch')

The attributes available on the Schematic object will depend on the contents
of the schematic, but in most cases you can expect a number of attributes, 
such as those listed below.

*DO* use a console and TAB-completion to explore the object.

sch.<TAB><TAB>  will show a number of members.  Some of most interest are likely


sch.symbol
sch.title_block
sch.text

but you'll also likely find

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
    print(component.property.Reference.value)

But often also as objects with attributes. For symbols (components) these are the
reference of the component.

Use tab-completion to see them all

sch.symbol.<TAB><TAB>

and use 'em.
sch.symbol.C42.dnp = True

That's the crash course: see the README and examples for more info.


Created on Jan 29, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com

'''
VERSION='0.2.2'
from skip.eeschema.schematic import Schematic, Symbol
from skip.pcbnew.pcb import PCB 
