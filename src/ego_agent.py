import sys

sys.path.append('/home/csreid/.pyenv/versions/3.10.12/lib/python3.10/site-packages')
sys.path.insert(0, '/home/csreid/CARLA_0.9.14/PythonAPI/carla')

import carla
from agents.navigation.basic_agent import BasicAgent
from agents.navigation.behavior_agent import BehaviorAgent
from custom_agent import ImitationAgent
import time
import numpy as np
import random
from utils.callback import ZMQCallback, GNSSCallback, IMUCallback, CameraCallback

def spawn_ego_agent(world, use_learned=False, socket=None, vehicle='micro.microlino', spawn_idx=None, randomize_spawn=False):
	bp_lib = world.get_blueprint_library()

	bp = bp_lib.find(f'vehicle.{vehicle}')
	bp.set_attribute('role_name', 'hero')
	if spawn_idx is None:
		spawn = random.choice(world.get_map().get_spawn_points())
	else:
		spawn = world.get_map().get_spawn_points()[spawn_idx]

	if randomize_spawn:
		#spawn.location = spawn.location + carla.Location(x=np.random.randint(0, 10), y=np.random.randint(0, 10))
		spawn.rotation = carla.Rotation(yaw=np.random.randint(0, 359))

	vehicle = world.spawn_actor(bp, spawn)

	camera_bp = bp_lib.find('sensor.camera.rgb')
	camera_bp.set_attribute('image_size_x', '256')
	camera_bp.set_attribute('image_size_y', '256')
	camera_bp.set_attribute('fov', '90')
	#camera_bp.set_attribute('sensor_tick', '0.1')

	imu_bp = bp_lib.find('sensor.other.imu')
	#imu_bp.set_attribute('sensor_tick', '0.1')
	gnss_bp = bp_lib.find('sensor.other.gnss')
	#gnss_bp.set_attribute('sensor_tick', '0.1')

	camera_transform = carla.Transform(carla.Location(y=1, z=1.5))
	camera1 = world.spawn_actor(camera_bp, camera_transform, attach_to=vehicle)

	camera_transform = carla.Transform(carla.Location(y=-1, z=1.5))
	camera2 = world.spawn_actor(camera_bp, camera_transform, attach_to=vehicle)

	imu = world.spawn_actor(imu_bp, carla.Transform(), attach_to=vehicle)
	gnss = world.spawn_actor(gnss_bp, carla.Transform(), attach_to=vehicle)

	# Spawn into given world and set a destination
	spawns = world.get_map().get_spawn_points()
	dest = random.choice(spawns).location
	if use_learned:
		agent = ImitationAgent(vehicle, socket)
	else:
		agent = BehaviorAgent(vehicle)

	return vehicle, agent, dest, [camera1, camera2, imu, gnss]
