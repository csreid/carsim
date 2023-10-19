from dataclasses import dataclass

@dataclass
class GNSSData:
  frame: int
  lat: float
  lon: float
  alt: float
