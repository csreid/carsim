from dataclasses import dataclass

@dataclass
class IMUData:
	frame: int
	acc_x: float
	acc_y: float
	acc_z: float
	ang_x: float,
	ang_y: float,
	ang_z: float
	compass: float
