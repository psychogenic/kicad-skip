'''
    A charlieplex type grid generator -- good example of creating wires, junctions, labels and tying them together.
    
    1)  Prepare a schematic with a standard Device:LED in it, set the footprint, MPN, any properties you want.
    
    2) run this script and pass it the schem path, then tell it where to save the result
    
    3) take a look
    

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com

'''
from skip import Symbol, Schematic

gridOrigin = (15, 10)
unitspace = 2.54

def units_to_mm(u:int):
    return u*unitspace

def to_grid(xunits:int, yunits:int):
    global unitspace, gridOrigin
    return ( (gridOrigin[0]*unitspace)+(xunits*unitspace), 
            (gridOrigin[1]*unitspace)+(yunits*unitspace))
            
def createLEDs(basedOn:Symbol, numrows:int, numcols:int, start_ref_count:int=1):
    '''
        Create a grid of closed based on some symbol
    '''
    dcount = start_ref_count
    table = []
    
    for row in range(numrows):
        column_leds = []
        for col in range(numcols):
            # clone the symbol
            newD = basedOn.clone()
            
            # set it's reference
            myref = f'D{dcount}'
            newD.property.Reference.value = myref
            # ugh kicad gets annoying with this when opening in eeschema
            # outside of a project--force all references to be this
            for ref in newD.getElementsByEntityType('reference'):
                ref.value = myref
                
            # move this component where we want it, on the grid
            coords = to_grid(col*7, row*6)
            newD.move(coords[0] - 1.27, coords[1])
            
            # keep track of LEDs we cloned
            column_leds.append(newD)
            
            dcount += 1
        
        table.append(column_leds)
            
    return table

def createAndWireLEDs(sch:Schematic, basedOn:Symbol, 
                      numrows:int, numcols:int, start_ref_count:int=1):
    '''
        Get the grid of cloned diodes, and wire them up, with junctions and labels.
    
    '''
    led_table = createLEDs(basedOn, numrows, numcols, start_ref_count)
    
    # make Ks in columns, As in rows
    an_wires = []
    cath_wires = []
    # for every LED, we're going to pull out the A pin over the LED and make
    # rows
    # we'll pull out K pin vertically and make columns
    for a_row in led_table:
        pu_wires = []
        
        cathode_wires = []
        for a_led in a_row:
            # depending on left or right orientation, we'll want to 
            # draw our wires ou
            awire_direction = -1 if a_led.at.value[2] == 180 else 1
            kwire_direction = -1 if awire_direction == 1 else 1
            
            # create a wire for the cathode
            # this wire has some random position/orientation, will set
            kwire = sch.wire.new()
            
            # start it on the location of the K pin, using named attribs here
            kwire.start_at(a_led.pin.K)
            
            # we want it horizontal
            kwire.delta_y = 0
            # we want it one grid space out, in the right direction
            kwire.delta_x = kwire_direction*unitspace
            # stash the wire
            cathode_wires.append(kwire)
            
            # for the anode, we'll make two wires, one straight out,
            # one upward
            
            # from the pin
            awire = sch.wire.new()
            awire.start_at(a_led.pin.A)
            awire.delta_y = 0 # keep it horizontal
            awire.delta_x = awire_direction*unitspace
            
            # from the end of that first wire, up by 3
            atorow = sch.wire.new()
            atorow.start_at(awire.end.value)
            atorow.delta_x = 0 # vertical
            atorow.delta_y = units_to_mm(-3)
            
            # remember these wires that pull up to the row
            pu_wires.append(atorow)
        
        # keep all the wires in lists, by row
        an_wires.append(pu_wires)
        cath_wires.append(cathode_wires)
    
    
    # now we want a big wire joining each row together
    row_count = 0
    for rw in an_wires:
        # create a wire from last "pu" wire of the row, going past first
        join_wire = sch.wire.new()
        join_wire.start_at(rw[-1].end.value) # starts on end point of last up wire in row
        
        # end it a bit past the first of those pull-up wires
        first_wire_conn_point = rw[0].end.value 
        join_wire.end_at([first_wire_conn_point[0] - units_to_mm(4), first_wire_conn_point[1]])
        # lets add some junctions
        for w in rw:
            junc = sch.junction.new()
            junc.move(w.end.value[0], w.end.value[1])
            
            
        # and finally, a global label attached to the end of our row joining wire
        row_count += 1
        lbl = sch.global_label.new()
        lbl.move(join_wire.end.value[0], join_wire.end.value[1])
        lbl.value = f'ROW_{row_count}'
        
    
    # ok, wire up the columns
    for col in range(numcols):
        
        first_wire = cath_wires[0][col]
        last_wire = cath_wires[-1][col]
        
        # we want a wire that goes down from first to past the bottom one
        join_wire = sch.wire.new()
        join_wire.start_at(first_wire.end.value)
        join_wire.delta_x = 0
        join_wire.delta_y = (last_wire.end.value[1] - first_wire.end.value[1]) + units_to_mm(4)
        
        # make it visible by playing with the width and style a bit
        join_wire.stroke.width.value = 0.4
        join_wire.stroke.type.value = 'dot'
        
        # add some junctions
        for rowidx in range(1, numrows):
            end_coords = cath_wires[rowidx][col].end.value
            junc = sch.junction.new()
            junc.move(end_coords[0], end_coords[1])
            
            
        # add a lable
        lbl = sch.global_label.new()
        lbl.move(join_wire.end.value[0], join_wire.end.value[1])
        lbl.value = f'COL_{col+1}'
        
    print(f'Done: created a {numrows}x{numcols} grid')
        





if __name__ == '__main__':
    schemfile = input("Path to a schematic with a LED in it (called DSOMETHING): ")
    if schemfile is not None and len(schemfile):
        schem = Schematic(schemfile)
        
        diodes = schem.symbol.reference_startswith('D')
        if not len(diodes):
            print("No 'D*' components found in schem")
        else:
            base_diode = diodes[0]
            print(f'Using diode {base_diode.property.Reference.value}')
            createAndWireLEDs(schem, base_diode, 10, 10, len(diodes))
            
            save_to = input("Path to save results to (empty to skip): ")
            if save_to is not None and len(save_to):
                schem.write(save_to)
                print("Done... check it out")
            
