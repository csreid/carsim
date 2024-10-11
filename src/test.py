from dotenv import load_dotenv
load_dotenv(override=True)

import carla
import random
import zmq
import json
import os
from datetime import datetime
import time
import pandas as pd
from dataclasses import dataclass, asdict
from pathlib import Path

from utils.remove_all_vehicles import remove_all_vehicles
from utils.messages.ground_truth import GroundTruthData
from ego_agent import spawn_ego_agent
from follow_ego_vehicle import follow_vehicle
from utils.callback import ZMQCallback, GNSSCallback, IMUCallback, CameraCallback
from agents.navigation.behavior_agent import BehaviorAgent

try:
	ctx = zmq.Context()
	sock = ctx.socket(zmq.SUB)
	sock.connect('tcp://127.0.0.1:5557')
	sock.setsockopt(zmq.SUBSCRIBE, b'act')

	server_url = os.environ['CARLA_SERVER']
	client = carla.Client(server_url, 2000)
	client.set_timeout(30.)
	#client.load_world('Town12')
	client.load_world('Town10HD')
	#client.load_world('Town04')
	world = client.get_world()
	print(world.get_map().name)
	debug = world.debug

	remove_all_vehicles(world)

	settings = world.get_settings()

	vehicle_blueprints = world.get_blueprint_library().filter('*vehicle*')

	sim_map = world.get_map().name
	spawn_points = world.get_map().get_spawn_points()

	# Spawn some traffic
	models = ['dodge', 'audi', 'model3', 'mini', 'mustang', 'lincoln', 'prius', 'nissan', 'crown', 'impala']
	blueprints = []
	for vehicle in world.get_blueprint_library().filter('*vehicle*'):
			if any(model in vehicle.id for model in models):
					blueprints.append(vehicle)

	# Set a max number of vehicles and prepare a list for those we spawn
	max_vehicles = 50
	max_vehicles = min([max_vehicles, len(spawn_points)])
	vehicles = []
	agents = []

	# Take a random sample of the spawn points and spawn some vehicles
	for i, spawn_point in enumerate(random.sample(spawn_points, max_vehicles)):
			temp = world.try_spawn_actor(random.choice(blueprints), spawn_point)
			if temp is not None:
					vehicles.append(temp)
					agents.append(BehaviorAgent(temp))

	# Spawn the ego agent
	while True:
		try:
			vehicle, agent, destination, [camera1, camera2, imu, gnss] = spawn_ego_agent(world, use_learned=True, socket=sock,) #spawn_idx=0)
			break
		except RuntimeError:
			print(f'Failed, gonna try again')
			pass

	agent.set_destination(destination)
	gnss_cb = GNSSCallback(ctx, rollout_id=0, type="gnss")
	imu_cb = IMUCallback(ctx, rollout_id=0, type="imu")
	camera_l_cb = CameraCallback(ctx, rollout_id=0, type="camera", img_type="rgb", camera_location="left")
	camera_r_cb = CameraCallback(ctx, rollout_id=0, type="camera", img_type="rgb", camera_location="right")
	ground_truth_cb = ZMQCallback(ctx, rollout_id=0, type="ground_truth")
	command_cb = ZMQCallback(ctx, rollout_id=0, type="command")
	tick_cb = ZMQCallback(ctx, rollout_id=0, type="tick")

	# Add callbacks to sensors
	camera1.listen(camera_l_cb)
	camera2.listen(camera_r_cb)
	imu.listen(imu_cb)
	gnss.listen(gnss_cb)
	#destination = carla.Location(x=222.635, y=-367.628, z=0.028)
	destination = random.choice(spawn_points).location
	agent.set_destination(destination)

	ctrl = carla.VehicleControl(throttle=1.)
	vehicle.apply_control(ctrl)

	snapshot = world.wait_for_tick()
	rollout_id = 0
	last_time = snapshot.timestamp.elapsed_seconds
	while True:
		snapshot = world.wait_for_tick()
		tick_cb({
			'ts': last_time
		})
		frame = snapshot.frame
		vel = vehicle.get_velocity()
		loc = vehicle.get_transform().location
		rot = vehicle.get_transform().rotation
		ang_vel = vehicle.get_angular_velocity()
		cmd = vehicle.get_control()

		if agent.done():
			destination = random.choice(spawn_points).location
			agent.set_destination(destination)

		gt_data = GroundTruthData(
			frame=frame,
			rollout_id=rollout_id,
			sim_timestamp=snapshot.timestamp.elapsed_seconds,
			x=loc.x,
			y=loc.y,
			z=loc.z,
			pitch=rot.pitch,
			yaw=rot.yaw,
			roll=rot.roll,
			vel_x=vel.x,
			vel_y=vel.y,
			vel_z=vel.z,
			ang_vel_x=ang_vel.x,
			ang_vel_y=ang_vel.y,
			ang_vel_z=ang_vel.z,
			throttle=cmd.throttle,
			steer=cmd.steer,
			brake=cmd.brake,
			dest_x=destination.x,
			dest_y=destination.y,
			dest_z=destination.z,
			is_done=False
		)

		cmd_data = {
			'frame': frame,
			'rollout_id': rollout_id,
			'sim_timestamp': snapshot.timestamp.elapsed_seconds,
			'throttle':  cmd.throttle,
			'steer': cmd.steer,
			'brake': cmd.brake
		}

		ground_truth_cb(asdict(gt_data))
		command_cb(cmd_data)

		last_time = snapshot.timestamp.elapsed_seconds
		ctrl = agent.run_step()
		vehicle.apply_control(ctrl)

		for veh, ai in zip(vehicles, agents):
			veh.apply_control(ai.run_step())

finally:
	remove_all_vehicles(world)
	world.tick()

	settings.synchronous_mode = False
	world.apply_settings(settings)
world.tick()

