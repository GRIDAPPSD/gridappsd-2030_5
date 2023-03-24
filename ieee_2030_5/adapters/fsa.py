import logging
from functools import lru_cache
from typing import Dict, List

import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m
from ieee_2030_5.adapters import AdapterListProtocol, BaseAdapter
from ieee_2030_5.types_ import Lfdi

_log = logging.getLogger(__name__)


__all__: List[str] = [
    "FSAAdapter"
]

class _FSAAdapter(BaseAdapter, AdapterListProtocol):
    def __init__(self) -> None:
        super().__init__()
        self._fsa: List[m.FunctionSetAssignments] = []
        # List of programs assigned to the index of a fsa
        self._programs: Dict[int, List[m.DERProgram]] = {}
            
    def fetch_all(self) -> List[m.FunctionSetAssignments]:
        return self._fsa
    
    def fetch_list(self, start: int = 0, after: int = 0, limit: int = 0) -> m.FunctionSetAssignmentsList:
        fsa_list = m.FunctionSetAssignmentsList(href=hrefs.fsa_href(), all=len(self._fsa), results=len(self._fsa),
                                                FunctionSetAssignments=self._fsa)
        
        return fsa_list
    
    def fetch_program_list(self, fsa_index: int, start: int = 0, after: int = 0, limit: int = 0) -> m.DERProgramList:
        all = len(self._programs[fsa_index])
        program_list = m.DERProgramList(href=hrefs.der_href(fsa_index=fsa_index),
                                        DERProgram=self._programs[fsa_index],
                                        all=all,
                                        results=all)
        return program_list
    
    def fetch_at(self, index: int) -> m.FunctionSetAssignments:
        return self._fsa[index]
    
    def add(self, fsa: m.FunctionSetAssignments) -> int:
        index = len(self._fsa)
        fsa.href = hrefs.fsa_href(index=index)
        return index
    
    def create(self, programs: List[m.DERProgram]) -> m.FunctionSetAssignments:
        fsa = m.FunctionSetAssignments(href=hrefs.fsa_href(index=len(self._fsa)))
        index = self.add(fsa)
        fsa.DERProgramListLink = m.DERProgramListLink(href=hrefs.der_href(fsa_index=index))
        self._programs[index] = programs
        return fsa
        
    
    
FSAAdapter = _FSAAdapter()