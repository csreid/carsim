def remove_all_vehicles(world):
    # Get the world and remove all vehicles
    vehicle_list = world.get_actors().filter('vehicle.*')
    ped_list = world.get_actors().filter('walker.*')
    for vehicle in vehicle_list:
        vehicle.destroy()

    for ped in ped_list:
        ped.destroy()

    print("All pedestrians and vehicles have been removed from the simulation.")

