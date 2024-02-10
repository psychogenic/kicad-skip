'''
    A charlieplex type grid generator -- good example of creating wires, junctions, labels and tying them together.
    
    1)  Prepare a schematic with a standard Device:LED in it, set the footprint, MPN, any properties you want.
    
    2) run this script and pass it the schem path, then tell it where to save the result
    
    3) take a look
    

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com

'''
from skip import Symbol, Schematic

gridOrigin = (18, 10)
unitspace = 2.54

def units_to_mm(u:int):
    return u*unitspace

def to_grid(xunits:int, yunits:int):
    global unitspace, gridOrigin
    return ( (gridOrigin[0]*unitspace)+(xunits*unitspace), 
            (gridOrigin[1]*unitspace)+(yunits*unitspace))
            
def createLEDs(basedOn:Symbol, numrows:int, numcols:int, charlie:bool, start_ref_count:int=1):
    '''
        Create a grid of closed based on some symbol
    '''
    dcount = start_ref_count
    table = []
    
    for row in range(numrows):
        column_leds = []
        for col in range(numcols):
            
            if charlie and col == row:
                # charlieplexing, skip dead led
                column_leds.append(None)
                continue
            # clone the symbol
            newD = basedOn.clone()
                
            # move this component where we want it, on the grid
            coords = to_grid(col*7, row*6)
            newD.move(coords[0] - 1.27, coords[1])
            
            # set it's reference (all of em!)
            newD.setAllReferences(f'D{dcount}')
            
            # keep track of LEDs we cloned
            column_leds.append(newD)
            
            dcount += 1
        
        table.append(column_leds)
            
    return table

def createAndWireLEDs(sch:Schematic, basedOn:Symbol, 
                      numrows:int, numcols:int, 
                      charlie:bool,
                      start_ref_count:int=1):
    '''
        Get the grid of cloned diodes, and wire them up, with junctions and labels.
    
    '''
    
    led_table = createLEDs(basedOn, numrows, numcols, charlie, start_ref_count)
    row_label_prefix = 'CHRLY' if charlie else 'ROW'
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
            if a_led is None:
                pu_wires.append(None)
                cathode_wires.append(None)
                continue
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
        
        endwire_idx = -1
        while rw[endwire_idx] is None:
            endwire_idx -= 1
        
        join_wire.start_at(rw[endwire_idx].end.value) # starts on end point of last up wire in row
        
        # end it a bit past the first of those pull-up wires
        firstwireidx = 0
        while rw[firstwireidx] is None:
            firstwireidx += 1
        first_wire_conn_point = rw[firstwireidx].end.value 
        join_wire.end_at([first_wire_conn_point[0] - units_to_mm(4), first_wire_conn_point[1]])
        # lets add some junctions
        for w in rw:
            if w is None:
                continue
            junc = sch.junction.new()
            junc.move(w.end.value[0], w.end.value[1])
            
            
        # and finally, a global label attached to the end of our row joining wire
        row_count += 1
        lbl = sch.global_label.new()
        lbl.move(join_wire.end.value[0], join_wire.end.value[1])
        lbl.value = f'{row_label_prefix}_{row_count}'
        
    # this is what we'll return, the wires that form the columns,
    # unlabeled
    column_wires = []
    # ok, wire up the columns
    for col in range(numcols):
        # end it a bit past the first of those pull-up wires
        firstwireidx = 0
        first_wire = cath_wires[firstwireidx][col]
        while first_wire is None:
            firstwireidx += 1
            first_wire = cath_wires[firstwireidx][col]
            
        lastwireidx = -1
        
        last_wire = cath_wires[lastwireidx][col]
        while last_wire is None:
            lastwireidx -= 1
            last_wire = cath_wires[lastwireidx][col]
        
        # we want a wire that goes down from first to past the bottom one
        join_wire = sch.wire.new()
        join_wire.start_at(first_wire.end.value)
        join_wire.delta_x = 0
        join_wire.delta_y = (last_wire.end.value[1] - first_wire.end.value[1]) + units_to_mm(4)
        
        # make it visible by playing with the width and style a bit
        join_wire.stroke.width.value = 0.4
        join_wire.stroke.type.value = 'dot'
        
        column_wires.append(join_wire)
        # add some junctions
        for rowidx in range(1, numrows):
            if cath_wires[rowidx][col] is None:
                continue
            end_coords = cath_wires[rowidx][col].end.value
            junc = sch.junction.new()
            junc.move(end_coords[0], end_coords[1])
            
        
    return column_wires
        

def createXYGrid(sch:Schematic, basedOn:Symbol, 
                      numrows:int, numcols:int, start_ref_count:int=1):
    
    column_wires = createAndWireLEDs(sch, basedOn, numrows, numcols, charlie=False, start_ref_count=start_ref_count)
    
    col_count = 0
    for join_wire in column_wires:
        # add a global label
        lbl = sch.global_label.new()
        lbl.move(join_wire.end.value[0], join_wire.end.value[1])
        lbl.value = f'COL_{col_count+1}'
        col_count += 1
        
    
    print(f'Done: created a {numrows}x{numcols} grid')
    

def createCharlieplex(sch:Schematic, basedOn:Symbol, 
                      numrows:int, numcols:int, start_ref_count:int=1):
    
    column_wires = createAndWireLEDs(sch, basedOn, numrows, numcols, charlie=True, start_ref_count=start_ref_count)
    
    col_count = 0
    for join_wire in column_wires:
        # add a global label
        lbl = sch.label.new()
        lbl.move(join_wire.end.value[0], join_wire.end.value[1], 90)
        lbl.value = f'CATH_{col_count+1}'
        col_count += 1
        
    row_labels = sch.global_label.value_startswith('CHRLY')
    for i in range(len(row_labels)):
        rowlbl = row_labels[i]
        lbl = sch.label.new()
        lbl.value = f'CATH_{i+1}'
        lbl.move(rowlbl.at.value[0] + units_to_mm(1), rowlbl.at.value[1])
        
    print(f'Done: created a {numrows}x{numcols} charlieplex')


if __name__ == '__main__':
    schemfile = input("Path to a schematic with a LED in it (called DSOMETHING): ")
    if schemfile is not None and len(schemfile):
        schem = Schematic(schemfile)
        
        diodes = schem.symbol.reference_startswith('D')
        if not len(diodes):
            print("No 'D*' components found in schem")
        else:
            
            base_diode = diodes[0]
            print(f'Using diode {base_diode.property.Reference.value}\n\n')
            
            
            grid_or_charly = input("Create XY grid (XY) or charlieplex (CP)?  [CP]: ")
            if len(grid_or_charly) == 0 or grid_or_charly.lower().startswith('c'):
                print("Creating charlieplex")
                createCharlieplex(schem, base_diode, 10, 10, len(diodes))
            else:
                print("Creating XY grid")
                createXYGrid(schem, base_diode, 10, 10, len(diodes))
            
            save_to = input("Path to save results to (empty to skip): ")
            if save_to is not None and len(save_to):
                schem.write(save_to)
                print("Done... check it out")
            
