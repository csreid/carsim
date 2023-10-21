from dotenv import load_dotenv
load_dotenv(override=True)

import carla
import random
import zmq
import os
from datetime import datetime
import pandas as pd
from dataclasses import dataclass, asdict
from pathlib import Path

from utils.remove_all_vehicles import remove_all_vehicles
from utils.messages.ground_truth import GroundTruthData
from ego_agent import spawn_ego_agent
from utils.callback import ZMQCallback, GNSSCallback, IMUCallback, CameraCallback


ctx = zmq.Context()
sock = ctx.socket(zmq.PUSH)
sock.bind('tcp://127.0.0.1:5555')

try:
	server_url = os.environ['CARLA_SERVER']
	print(server_url)
	client = carla.Client(server_url, 2000)
	world = client.get_world()
	tm = client.get_trafficmanager(8000)

	remove_all_vehicles(world)

	settings = world.get_settings()
	settings.synchronous_mode = True
	settings.fixed_delta_seconds=1./20.

	world.apply_settings(settings)

	tm.set_global_distance_to_leading_vehicle(5.0)
	tm.set_synchronous_mode(True)

	world.tick()

	vehicle_blueprints = world.get_blueprint_library().filter('*vehicle*')

	sim_map = world.get_map().name
	spawn_points = world.get_map().get_spawn_points()

	destination = random.choice(spawn_points).location
	world.tick()
	vehicle, agent, destination, sensors = spawn_ego_agent(world, sock, spawn_idx=0)
	agent.set_destination(destination)
	world.tick()

	ground_truth_cb = ZMQCallback(sock, type="ground_truth")
	command_cb = ZMQCallback(sock, type="command")
	#Spawn NPC Cars
	for i in range(20):
		npc = world.try_spawn_actor(random.choice(vehicle_blueprints), random.choice(spawn_points))
		if npc:
			npc.set_autopilot(True, tm.get_port())

	for i in range(20000):
		if (i % 100) == 0:
			print(i)
		frame = world.tick()
		cmd = vehicle.get_control()
		vel = vehicle.get_velocity()
		loc = vehicle.get_transform().location
		rot = vehicle.get_transform().rotation
		ang_vel = vehicle.get_angular_velocity()

		gt_data = GroundTruthData(
			frame=frame,
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
			dest_z=destination.z
		)

		cmd_data = {
			'frame': frame,
			'throttle':  cmd.throttle,
			'steer': cmd.steer,
			'brake': cmd.brake
		}
		ground_truth_cb(asdict(gt_data))
		command_cb(cmd_data)

		# Step the simulation
		if agent.done():
			destination = random.choice(spawn_points).location
			agent.set_destination(destination)
		vehicle.apply_control(agent.run_step())

finally:
	remove_all_vehicles(world)
	world.tick()

	settings.synchronous_mode = False
	tm.set_synchronous_mode(False)
	world.apply_settings(settings)
	world.tick()
