from ieee_2030_5.models import DER
from dataclasses import dataclass

class DERWithDescription(DER):
    def __init__(self, description: str, **kwargs):
        super().__init__(**kwargs)
        self.description = description

    def wrapped(self) -> DER:
        kwargs = self.__dict__.copy()
        del kwargs['description']
        return DER(**kwargs)