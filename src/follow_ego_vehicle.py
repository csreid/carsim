import carla
import os
import time

def follow_vehicle():
	server_url = 'localhost'
	client = carla.Client(server_url, 2000)
	world = client.get_world()

	# Create the spectator camera
	spectator = world.get_spectator()
	vehicle = None
	for actor in world.get_actors():
		if actor.attributes.get('role_name') == 'hero':
			vehicle = actor

	while True:
		# Get the current transform of the vehicle
		if vehicle is None:
			for actor in world.get_actors():
				if actor.attributes.get('role_name') == 'hero':
					vehicle = actor
			continue

		spectator = world.get_spectator()
		vehicle_transform = vehicle.get_transform()

		# Set the spectator camera's transform to follow the vehicle
		spectator.set_transform(
			carla.Transform(
				vehicle_transform.location + carla.Location(z=30),
				carla.Rotation(pitch=-90)
			)
		)

		if vehicle.get_transform() == carla.Transform():
			vehicle = None
		time.sleep(1/60.)

if __name__ == '__main__':
	follow_vehicle()
