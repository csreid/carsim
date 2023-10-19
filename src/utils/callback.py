import zmq
import json
from dataclasses import asdict

class ZMQCallback():
	def __init__(self, sock, **kwargs):
		self._kwargs = kwargs
		self._sock = sock

	def send(self, data):
		self._sock.send(bytes(json.dumps({**data, **self._kwargs}), 'utf-8'))

	def __call__(self, data):
		return self.send(data)

class _SensorCallback(ZMQCallback):
	def get_sensor_data(self, data):
		return {}

	def _get_common_data(self, data):
		return {**{ "frame": data.frame }, **self._kwargs}

	def send(self, data):
		common_data = self._get_common_data(data)
		sensor_data = self.get_sensor_data(data)

		data = {**common_data, **sensor_data}
		return super().send(data)

class IMUCallback(_SensorCallback):
	def get_sensor_data(self, data):
		acc_x, acc_y, acc_z = (
			data.accelerometer.x,
			data.accelerometer.y,
			data.accelerometer.z
		)

		ang_x, ang_y, ang_z = (
			data.gyroscope.x,
			data.gyroscope.y,
			data.gyroscope.z,
		)

		compass = data.compass
		return {
				'acc_x': acc_x,
				'acc_y': acc_y,
				'acc_z': acc_z,
				'ang_x': ang_x,
				'ang_y': ang_y,
				'ang_z': ang_z,
				'compass': compass
		}

class GNSSCallback(_SensorCallback):
	def get_sensor_data(self, data):
		lat, lon, alt = (
			data.latitude,
			data.longitude,
			data.altitude
		)

		return {
			"lat": lat,
			"lon": lon,
			"alt": alt
		}

class CameraCallback(_SensorCallback):
	def get_sensor_data(self, data):
		width, height = (data.width, data.height)
		img_bytes = data.raw_data

		return {
			"width": width,
			"height": height,
			"bytes": img_bytes.tobytes().hex()
		}
