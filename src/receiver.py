from dotenv import load_dotenv
load_dotenv()
import os
import zmq
import json
import psycopg2
from psycopg_pool import ConnectionPool
import time
import numpy as np

### This is chock full of bad database stuff.
### I know, I know, I'll get there

#conn = psycopg2.connect(os.environ.get("DBSTRING"))

def handle_imu(data, conn):
	cur = conn.cursor()

	cur.execute(f"""
		insert into imu_data (
			frame,
			sim_id,
			sim_timestamp,
			acc_x, acc_y, acc_z,
			ang_x, ang_y, ang_z,
			compass
		) values (
			{data['frame']},
			'{data['sim_id']}',
			{data['sim_timestamp']},
			{data['acc_x']}, {data['acc_y']}, {data['acc_z']},
			{data['ang_x']}, {data['ang_y']}, {data['ang_z']},
			{data['compass']}
		);
	""")

	conn.commit()
	cur.close()

def handle_gnss(data, conn):
	cur = conn.cursor()

	cur.execute(f"""
		insert into gnss_data (
			frame,
			sim_id,
			sim_timestamp,
			lat,
			lon,
			alt
		) values (
			{data['frame']},
			'{data['sim_id']}',
			{data['sim_timestamp']},
			{data['lat']}, {data['lon']}, {data['alt']}
		);
	""")
	conn.commit()
	cur.close()

def handle_camera(data, conn):
	cur = conn.cursor()

	cur.execute(f"""
		insert into camera_data (
			frame,
			sim_id,
			sim_timestamp,
			width,
			height,
			image,
			camera_type,
			camera_loc
		) values (
			{data['frame']},
			'{data['sim_id']}',
			{data['sim_timestamp']},
			{data['width']}, {data['height']},
			%s,
			'{data['img_type']}',
			'{data['camera_location']}'
		);
		""",
		(bytes.fromhex(data['bytes']),)
	)
	conn.commit()
	cur.close()

def handle_ground_truth(data, conn):
	cur = conn.cursor()

	cur.execute(f"""
		insert into ground_truth (
			frame,
			sim_id,
			sim_timestamp,
			x,
			y,
			z,
			pitch,
			yaw,
			roll,
			vel_x,
			vel_y,
			vel_z,
			ang_vel_x,
			ang_vel_y,
			ang_vel_z,
			dest_x,
			dest_y,
			dest_z
		) values (
			{data['frame']},
			'{data['sim_id']}',
			{data['sim_timestamp']},
			{data['x']}, {data['y']}, {data['z']},
			{data['pitch']}, {data['yaw']}, {data['roll']},
			{data['vel_x']}, {data['vel_y']}, {data['vel_z']},
			{data['ang_vel_x']}, {data['ang_vel_y']}, {data['ang_vel_z']},
			{data['dest_x']}, {data['dest_y']}, {data['dest_z']}
		);
	""")
	conn.commit()
	cur.close()

def handle_command(data, conn):
	cur = conn.cursor()

	cur.execute(f"""
		insert into commands (
			frame,
			sim_id,
			sim_timestamp,
			throttle,
			steer,
			brake
		) values (
			{data['frame']},
			'{data['sim_id']}',
			{data['sim_timestamp']},
			{data['throttle']}, {data['steer']}, {data['brake']}
		);
	""")
	conn.commit()
	cur.close()

def main():
	ctx = zmq.Context()
	receiver = ctx.socket(zmq.PULL)
	receiver.bind('tcp://127.0.0.1:5555')

	count = 0
	times = []
	with ConnectionPool(os.environ.get("DBSTRING"), max_size=16) as pool:
		while True:
			count += 1
			with pool.connection() as conn:
				data = receiver.recv_json()
				curtime = time.time()
				try:
					if data['type'] == 'imu':
						handle_imu(data, conn)
					elif data['type'] == 'gnss':
						handle_gnss(data, conn)
					elif data['type'] == 'camera':
						handle_camera(data, conn)
					elif data['type'] == 'ground_truth':
						handle_ground_truth(data, conn)
					elif data['type'] == 'command':
						handle_command(data, conn)
				except Exception as e:
					print(f'Failed to write something: {e}')

			endtime = time.time()
			times.append(endtime - curtime)
			if (count % 100) == 0:
				print(f'Latency over the last 100: {np.min(times) * 1000:.4}ms < {(np.mean(times)*1000):.4}ms < {(np.max(times)*1000):.4}ms')
				times = []

if __name__ == '__main__':
	main()
