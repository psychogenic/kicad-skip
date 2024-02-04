# kicad skip: S-expression kicad file python parser

Copyright &copy; 2024 Pat Deegan, [psychogenic.com](https://psychogenic.com/)


This library is focused on scripted manipulations of schematics (and other) kicad  _source_ _files_  
and allows any item to be edited in a hopefully intuitive way.

It also provides helpers for common operations.


Kicad schematic, layout and other files are stored as trees of s-expressions, like

```
(kicad_sch (version 20230121) (generator eeschema)
  (uuid 20adca1d-43a1-4784-9682-8b7dd1c7d330)
  (title_block (title "My Demo Board") (date "2024-01-31") (rev "1.0.5")
    (company "Psychogenic Technologies") (comment 1 "(C) 2023, 2024 Pat Deegan")
  )
  (lib_symbols
    (symbol "74xx:74CBTLV3257" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 17.78 1.27 0) (effects (font (size 1.27 1.27))))
      (property "Value" "74CBTLV3257" (at 15.24 -1.27 0)(effects (font (size 1.27 1.27))))
  ...
  (symbol (lib_id "SomeLib:Partname") (at 317.5 45.72 0) (unit 1)
    (in_bom yes) (on_board yes) (dnp no)
    (uuid 342c76f3-b2b8-40b2-a0b0-d83e480188cc)
    (property "Reference" "J4" (at 311.15 29.21 0)(effects (font (size 1.27 1.27))))
    (property "Value" "TT04_BREAKOUT_REVB" (at 317.5 76.2 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "TinyTapeout:TT04_BREAKOUT_SMB" (at 320.04 81.28 0)
    (effects (font (size 1.27 1.27)) hide))
    (pin "A1" (uuid 5132b98d-ec39-4a2b-974d-c4d323ea43eb))
    (pin "A10" (uuid bf1f9b27-0b93-4778-ac69-684e16bea09c))
    (pin "A19" (uuid 43e3e4f6-008a-4ddf-a427-4414db85dcbb))
  ...
```
which are great for machine parsing, but not so much for a quick scripted manipulation.

With skip, you can quickly explore and modify the contents of a schematic (or, really, any
kicad s-expression file).


## Examples

Effort has been made to make exploring the contents easy.  This means:

#### named attributes 
Where possible, collections have named attributes: **do use** TAB-completion, schem.<TAB><TAB> etc

Examples

```
>>> schem.symbol.U TAB TAB
```
outputs (something like, depending on schematic):

```
  schem.symbol.U1          schem.symbol.U3          schem.symbol.U4_B        schem.symbol.U4_D               
  schem.symbol.U2          schem.symbol.U4_A        schem.symbol.U4_C        schem.symbol.U4_E
```

and

``` 
>>> schem.symbol.U1.property. TAB TAB
```

outputs

```
 schem.symbol.U1.property.Characteristics           
 schem.symbol.U1.property.Datasheet                  
 schem.symbol.U1.property.DigikeyPN                  
 schem.symbol.U1.property.Footprint                  
 schem.symbol.U1.property.MPN                        
 schem.symbol.U1.property.Reference                
 schem.symbol.U1.property.Value    
```

#### representation
`__repr__` and `__str__` overrides so you have an idea what you're looking at.  Just enter the variable in the REPL console and it should spit something sane out.

 
```
>>> schem
<Schematic 'samp/my_schematic.kicad_sch'>

>>> schem.symbol[23]
<symbol C28>

>>> schem.symbol[23].property
<Collection [<PropertyString Reference = 'C28'>, <PropertyString Value = '100nF'>, 
 <PropertyString Footprint = 'Capacitor_SMD:C_0402_1005Metric'>, 
 <PropertyString Datasheet = '~'>, <PropertyString JLC = ''>, 
 <PropertyString Part_number = ''>, <PropertyString MPN = 'CL05A104KA5NNNC'>, 
 <PropertyString Characteristics = '100n 10% 25V XR 0402'>, 
 <PropertyString MPN_ALT = 'GRM155R71E104KE14J'>]>

>>> schem.wire[22]
<Wire [314.96, 152.4] - [317.5, 152.4]>

>>> schem.text[4]
<text 'Options fo...'>

# and much more, e.g. for library symbols, junctions, labels, whatever's in there 
```


## Quick walkthrough

Here's some sample interaction with the library.  The basic functions allow you to view and edit attributes.  More involved helpers let you search and crawl the schematic to find things.


#### basic

```
# load a schematic
schem = skip.Schematic('samp/my_schem.kicad_sch')

# loop over all components, treat collection as array
for component in schem.symbol:
    component # do something 

# search through the symbols by reference or value, using regex or starts_with
>>> schem.symbol.reference_matches(r'(C|R)2[158]')
[<symbol C25>, <symbol C28>, <symbol R25>, <symbol C21>, <symbol R21>, <symbol R28>]

>>> sorted(schem.symbol.value_startswith('10k'))
[<symbol R12>, <symbol R30>, <symbol R31>, <symbol R32>, <symbol R33>, <symbol R42>, 
 <symbol R43>, <symbol R44>, <symbol R45>, <symbol R46>, <symbol R47>, <symbol R48>, 
 <symbol R8>, <symbol R9>]

# or refer to components by name
conn = schem.symbol.J15

# symbols have attributes
if not conn.in_bom:
    conn.dnp = True 

# and properties (things that can be named by user)
for p in conn.property:
    print(f'{p.name} = {p.value}')
# will output "Reference = J15", "MPN = USB4500-03-0-A" etc

# and change properties, of course
>>> conn.property.MPN.value = 'ABC123'
>>> conn.property.MPN
<PropertyString MPN = 'ABC123'>



# clone pretty much anything and modify it
>>> mpn_alt = conn.property.MPN.clone()
>>> mpn_alt.name = 'MPN_ALT'
>>> mpn_alt.value = 'ABC456'


# save the result
>>> schem.write('/tmp/newfile.kicad_sch')

# let's verify the change
>>> schem.read('/tmp/newfile.kicad_sch')
>>> conn = schem.symbol.J15
>>> for p in conn.property:
        p
<PropertyString Reference = 'J15'>
<PropertyString Value = 'USB4500-03-0-A_REVA'>
<PropertyString MPN = 'ABC123'>
<PropertyString MPN_ALT = 'ABC456'>

```


### Helpers

Collections, and the source file object, have helpers to locate relevant elements.

#### Attached elements

Where applicable, such as for symbols (components), directly attached elements (via wires) 
may be listed using attached_*

```
>>> conn = sch.symbol.J15

>>> conn.attached_ TAB TAB
 conn.attached_all            
 conn.attached_global_labels  
 conn.attached_labels         
 conn.attached_symbols        
 conn.attached_wires
>>> conn.attached_symbols
 [<symbol C3>, <symbol R16>, <symbol C47>, 
  <symbol R20>, <symbol C46>, <symbol R21>, 
  <symbol F1>]

>>> conn.attached_labels
 [<label CC2>, <label CC1>]
 
# or list everything attached
>>> conn.attached_all
 [<symbol C3>, <symbol R16>, <symbol C47>, 
  <symbol R20>, <symbol C46>, <symbol R21>, 
  <symbol F1>, <global_label usb_d->, 
  <global_label usb_d+>, <label CC2>, 
  <label CC1>]

```

#### finding elements

Symbols may be located by reference or value

  *  schem.symbol.reference_matches(REGEX)
  
  *  schem.symbol.reference_startswith(STR)
  
In addition, containers with 'positionable' elements have

  * within_circle(X, Y, RADIUS)
  
  * within_rectangle(X1, Y1, X2, Y2)
  
  * within_reach_of(ELEMENT, RADIUS) # circle around ELEMENT's position
  
  * between_elements(ELEMENT1, ELEMENT2) # within rectangle formed by two elements
  
A collection will only return results of it's own type (e.g. global_labels.within_circle() will only return global labels).

To search the entire schematic, the same within* and between() methods exist on the source file object (the schem, here).
This will return any label, global label or symbol with the constrained bounds.

```

>>> schem.global_label.between_elements(sch.symbol.C49, sch.symbol.R16)
 [<global_label usb_d->, <global_label usb_d+>, 
  <global_label usb_d+>, <global_label usb_d->]
>>> 
>>> schem.between_elements(sch.symbol.C49, sch.symbol.R16)
 [<symbol C44>, <symbol #PWR0121>, <symbol J15>, 
  <symbol C47>, <symbol #PWR0122>, <symbol D5>, <symbol C48>, 
  <symbol C45>, <symbol #PWR021>, <symbol C49>, <symbol R20>, 
  <symbol C46>, <symbol #FLG02>, <symbol F1>, <symbol C3>, 
  <symbol R16>, <symbol R21>, <symbol D6>, <label CC2>, 
  <label CC1>, <label vfused>, <global_label usb_d->, 
  <global_label usb_d+>, <global_label usb_d+>, 
  <global_label usb_d->]

```

## API

Further documentation to come.  For now, use the above, load a schematic in a console, and explore what's available using TAB-/code-completion.


### Notes

The main thing to note is that the leaves of the tree usually have a ".value" that should be used to access the actual contents and, especially, for setting values. 

Also, some elements have a position, and these can be moved or translated a certain amount

  *  element.move(x, y, [rotation])
  
  *  element.translation(deltax, deltay)

Finally, lots of these things are really deep--constructing from scratch is not the best idea.  Use

  * element.clone()
  
and edit the returned copy.  Cloned elements will be at the level of their source--e.g. a cloned property will be in the symbol it was cloned from.  



Have fun.

2024-04-04
Pat Deegan 


