'''
Created on Jan 30, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from skip.property.property import ElementWithPropertiesWrapper
from skip.sexp.parser import ParsedValue

class SheetWrapper(ElementWithPropertiesWrapper):
    def __init__(self, pv:ParsedValue):
        super().__init__(pv)