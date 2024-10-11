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
import uuid

from utils.remove_all_vehicles import remove_all_vehicles
from utils.messages.ground_truth import GroundTruthData
from ego_agent import spawn_ego_agent
from utils.callback import ZMQCallback, GNSSCallback, IMUCallback, CameraCallback

def begin_new_rollout(agent):
	rollout_id = str(uuid.uuid4())
	print(f'Starting rollout {rollout_id}')
	# Set up sensor callbacks
	gnss_cb = GNSSCallback(
		ctx,
		rollout_id=rollout_id,
		type="gnss"
	)
	imu_cb = IMUCallback(
		ctx,
		rollout_id=rollout_id,
		type="imu"
	)
	camera_l_cb = CameraCallback(
		ctx,
		rollout_id=rollout_id,
		type="camera",
		img_type="rgb",
		camera_location="left"
	)
	camera_r_cb = CameraCallback(ctx, rollout_id=rollout_id, type="camera", img_type="rgb", camera_location="right")

	# Stop old sensors
	for sensor in [camera1, camera2, imu, gnss]:
		if sensor.is_listening():
			sensor.stop()

	# Add callbacks to sensors
	camera1.listen(camera_l_cb)
	camera2.listen(camera_r_cb)
	imu.listen(imu_cb)
	gnss.listen(gnss_cb)

	destination = random.choice(spawn_points).location
	agent.set_destination(destination)

	return rollout_id

try:
	ctx = zmq.Context()
	server_url = os.environ['CARLA_SERVER']
	client = carla.Client(server_url, 2000)
	client.load_world('Town10HD')
	world = client.get_world()

	remove_all_vehicles(world)

	settings = world.get_settings()
	#settings.fixed_delta_seconds = 0.05
	#world.apply_settings(settings)

	vehicle_blueprints = world.get_blueprint_library().filter('*vehicle*')

	sim_map = world.get_map().name
	spawn_points = world.get_map().get_spawn_points()

	destination = random.choice(spawn_points).location
	vehicle, agent, destination, [camera1, camera2, imu, gnss] = spawn_ego_agent(world, spawn_idx=1)
	print(f'Ego vehicle id: {vehicle}')

	snapshot = world.wait_for_tick()
	last_time = snapshot.timestamp.elapsed_seconds
	rollout_id = begin_new_rollout(agent)

	ground_truth_cb = ZMQCallback(ctx, rollout_id=rollout_id, type="ground_truth")
	command_cb = ZMQCallback(ctx, rollout_id=rollout_id, type="command")
	tick_cb = ZMQCallback(ctx, rollout_id=rollout_id, type="tick")
	while True:
		snapshot = world.wait_for_tick()
		tick_cb({
			'ts': last_time
		})
		frame = snapshot.frame
		if (snapshot.timestamp.elapsed_seconds - last_time) >= 0.05:
			cmd = vehicle.get_control()
			vel = vehicle.get_velocity()
			loc = vehicle.get_transform().location
			rot = vehicle.get_transform().rotation
			ang_vel = vehicle.get_angular_velocity()

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
				is_done= agent.done()
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

		# Step the simulation
		if agent.done():
			begin_new_rollout(agent)

		action = agent.run_step()
		vehicle.apply_control(action)

finally:
	remove_all_vehicles(world)
	world.tick()

	settings.synchronous_mode = False
	world.apply_settings(settings)
	world.tick()
