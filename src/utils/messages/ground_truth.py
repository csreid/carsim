from dataclasses import dataclass

@dataclass
class GroundTruthData:
    frame: int
    x: float
    y: float
    z: float
    pitch: float
    roll: float
    yaw: float
    vel_x: float
    vel_y: float
    vel_z: float
    ang_vel_x: float
    ang_vel_y: float
    ang_vel_z: float
    dest_x: float
    dest_y: float
    dest_z: float
    throttle: float
    steer: float
    brake: float
