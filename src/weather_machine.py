import numpy as np
from enum import Enum
from carla import WeatherParameters

class TimeOfDay(Enum):
    NOON= 0
    SUNSET= 1

class Weather(Enum):
    CLEAR= 0
    CLOUDY= 1
    SOFTRAIN= 6
    MIDRAIN= 4
    HARDRAIN= 5
    CLEARWET= 2
    CLOUDYWET= 3

class WeatherStateMachine:
    def __init__(self, initial=Weather.CLEAR):
        self.state = initial
        self.probabilities = {
            Weather.CLEAR: {
                Weather.CLEAR: 0.99,
                Weather.CLOUDY: 0.01
            },
            Weather.CLOUDY: {
                Weather.CLOUDY: 0.98,
                Weather.CLEAR: 0.001,
                Weather.SOFTRAIN: 0.015,
                Weather.MIDRAIN: 0.004
            },
            Weather.SOFTRAIN: {
                Weather.SOFTRAIN: 0.99,
                Weather.MIDRAIN: 0.005,
                Weather.CLOUDYWET: 0.005
            },
            Weather.MIDRAIN: {
                Weather.MIDRAIN: 0.99,
                Weather.SOFTRAIN: 0.005,
                Weather.HARDRAIN: 0.005,
            },
            Weather.HARDRAIN: {
                Weather.HARDRAIN: 0.99,
                Weather.MIDRAIN: 0.01
            },
            Weather.CLOUDYWET: {
                Weather.CLOUDYWET: 0.98,
                Weather.CLEARWET: 0.005,
                Weather.SOFTRAIN: 0.005,
                Weather.MIDRAIN: 0.01
            },
            Weather.CLEARWET: {
                Weather.CLEARWET: 0.99,
                Weather.CLOUDYWET: 0.005,
                Weather.CLEAR: 0.005
            }
        }

    def transition(self):
        possible_landings = [
            k
            for k
            in self.probabilities[self.state].keys()
        ]
        transition_probabilities = [
            p
            for p
            in self.probabilities[self.state].values()
        ]
        self.state = np.random.choice(
            possible_landings,
            p=transition_probabilities
        )

        return self.state


state_map = {
    TimeOfDay.NOON: {
        Weather.CLEAR: WeatherParameters.ClearNoon,
        Weather.CLOUDY: WeatherParameters.ClearNoon,
        Weather.CLEARWET: WeatherParameters.WetNoon,
        Weather.CLOUDYWET: WeatherParameters.WetCloudyNoon,
        Weather.MIDRAIN: WeatherParameters.MidRainyNoon,
        Weather.HARDRAIN: WeatherParameters.HardRainNoon,
        Weather.SOFTRAIN: WeatherParameters.SoftRainNoon
    },
    TimeOfDay.SUNSET: {
        Weather.CLEAR: WeatherParameters.ClearSunset,
        Weather.CLOUDY: WeatherParameters.ClearSunset,
        Weather.CLEARWET: WeatherParameters.WetSunset,
        Weather.CLOUDYWET: WeatherParameters.WetCloudySunset,
        Weather.MIDRAIN: WeatherParameters.MidRainSunset,
        Weather.HARDRAIN: WeatherParameters.HardRainSunset,
        Weather.SOFTRAIN: WeatherParameters.SoftRainSunset
    }
}
class WeatherController:
    def __init__(self, time_of_day: TimeOfDay=TimeOfDay.NOON):
        self.time_of_day = time_of_day
        self.weather_machine = WeatherStateMachine()

    def step(self):
        weather = self.weather_machine.transition()
        return state_map[self.time_of_day][weather]
