import sys

import carla
from agents.navigation.basic_agent import BasicAgent
from agents.navigation.behavior_agent import BehaviorAgent
import time
import numpy as np
import random
from utils.callback import ZMQCallback, GNSSCallback, IMUCallback, CameraCallback

def spawn_ego_agent(world, zmq_sock, vehicle='micro.microlino', spawn_idx=None):
	bp_lib = world.get_blueprint_library()

	bp = bp_lib.find(f'vehicle.{vehicle}')
	bp.set_attribute('role_name', 'hero')
	if spawn_idx is None:
		spawn = random.choice(world.get_map().get_spawn_points())
	else:
		spawn = world.get_map().get_spawn_points()[spawn_idx]

	world.tick()

	vehicle = world.spawn_actor(bp, spawn)

	world.tick()

	camera_bp = bp_lib.find('sensor.camera.rgb')
	camera_bp.set_attribute('image_size_x', '256')
	camera_bp.set_attribute('image_size_y', '256')
	camera_bp.set_attribute('fov', '90')

	imu_bp = bp_lib.find('sensor.other.imu')
	gnss_bp = bp_lib.find('sensor.other.gnss')

	camera_transform = carla.Transform(carla.Location(y=1, z=1.5))
	camera1 = world.spawn_actor(camera_bp, camera_transform, attach_to=vehicle)
	world.tick()

	camera_transform = carla.Transform(carla.Location(y=-1, z=1.5))
	camera2 = world.spawn_actor(camera_bp, camera_transform, attach_to=vehicle)
	world.tick()

	imu = world.spawn_actor(imu_bp, carla.Transform(), attach_to=vehicle)
	gnss = world.spawn_actor(gnss_bp, carla.Transform(), attach_to=vehicle)
	world.tick()

	# Set up sensor callbacks
	gnss_cb = GNSSCallback(zmq_sock, type="gnss")
	imu_cb = IMUCallback(zmq_sock, type="imu")

	camera_l_cb = CameraCallback(zmq_sock, type="camera", img_type="rgb", camera_location="left")
	camera_r_cb = CameraCallback(zmq_sock, type="camera", img_type="rgb", camera_location="right")

	spawns = world.get_map().get_spawn_points()
	dest = random.choice(spawns).location

	agent = BehaviorAgent(vehicle, behavior='aggressive')
	agent.set_destination(dest)
	world.tick()

	return vehicle, agent, dest
