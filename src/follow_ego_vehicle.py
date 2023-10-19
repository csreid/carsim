import carla
import time

def follow_vehicle(world, vehicle_id):
    # Get the spawned vehicle by its ID
    vehicle = world.get_actor(vehicle_id)

    # Create the spectator camera
    spectator = world.get_spectator()

    while True:
        # Get the current transform of the vehicle
        vehicle_transform = carla.Transform(carla.Location(x=100, y=200, z=0), carla.Rotation())

        # Set the spectator camera's transform to follow the vehicle
        spectator.set_transform(
            carla.Transform(vehicle_transform.location + carla.Location(z=30),
                            carla.Rotation(pitch=-90)))

        # Sleep for a small interval
        time.sleep(0.01)

if __name__ == '__main__':
    vehicle_id = 123  # Replace with the actual ID of the vehicle to follow
    follow_vehicle(vehicle_id)
