from agents.navigation.basic_agent import BasicAgent
import carla
import zmq
import json
import time

class ImitationAgent(BasicAgent):
	def __init__(self, vehicle, socket):
		self._sock = socket
		self.vehicle = vehicle

		self._dest = None
		self._prevtime = None
		self._curact = carla.VehicleControl(
			throttle=0.,
			steer=0.,
			brake=1.,
		)

	def set_destination(self, dest):
		self._dest = dest

	def done(self):
		return False

	def _should_get_new_action(self):
		return True

	def run_step(self, debug=False):
		try:
			packet = self._sock.recv_multipart(flags=zmq.NOBLOCK)
			action = json.loads(packet[1].decode('utf-8'))
		except zmq.error.Again as e:
			return self._curact
		pred_throttle = max(0, action['throttle'])
		pred_steer = action['steer']
		pred_brake = max(0, action['brake'])

		self._curact = carla.VehicleControl(
			throttle=pred_throttle,
			steer=pred_steer,
			brake=pred_brake
		)

		return self._curact
