import os
import zmq
import json
import psycopg2

### This is chock full of bad database stuff.
### I know, I know, I'll get there

conn = psycopg2.connect(os.environ.get("DBSTRING"))
def handle_imu(data):
	cur = conn.cursor()

	cur.execute(f"""
		insert into imu_data (
			frame,
			acc_x, acc_y, acc_z,
			ang_x, ang_y, ang_z,
			compass
		) values (
			{data['frame']},
			{data['acc_x']}, {data['acc_y']}, {data['acc_z']},
			{data['ang_x']}, {data['ang_y']}, {data['ang_z']},
			{data['compass']}
		);
	""")

	conn.commit()
	cur.close()

def handle_gnss(data):
	cur = conn.cursor()

	cur.execute(f"""
		insert into gnss_data (
			frame,
			lat,
			lon,
			alt
		) values (
			{data['frame']},
			{data['lat']}, {data['lon']}, {data['alt']}
		);
	""")
	conn.commit()
	cur.close()

def handle_camera(data):
	cur = conn.cursor()

	cur.execute(f"""
		insert into camera_data (
			frame,
			width,
			height,
			image,
			camera_type,
			camera_loc
		) values (
			{data['frame']},
			{data['width']}, {data['height']},
			'{data['bytes']}',
			'{data['img_type']}',
			'{data['camera_location']}'
		);
	""")
	conn.commit()
	cur.close()

def handle_ground_truth(data):
	cur = conn.cursor()

	cur.execute(f"""
		insert into ground_truth (
			frame,
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
			{data['x']}, {data['y']}, {data['z']},
			{data['pitch']}, {data['yaw']}, {data['roll']},
			{data['vel_x']}, {data['vel_y']}, {data['vel_z']},
			{data['ang_vel_x']}, {data['ang_vel_y']}, {data['ang_vel_z']},
			{data['dest_x']}, {data['dest_y']}, {data['dest_z']}
		);
	""")
	conn.commit()
	cur.close()

def handle_command(data):
	cur = conn.cursor()

	cur.execute(f"""
		insert into commands (
			frame,
			throttle,
			steer,
			brake
		) values (
			{data['frame']},
			{data['throttle']}, {data['steer']}, {data['brake']}
		);
	""")
	conn.commit()
	cur.close()

def main():
	ctx = zmq.Context()
	receiver = ctx.socket(zmq.PULL)
	receiver.connect('tcp://127.0.0.1:5555')

	while True:
		data = receiver.recv_json()
		if data['type'] == 'imu':
			handle_imu(data)
		elif data['type'] == 'gnss':
			handle_gnss(data)
		elif data['type'] == 'camera':
			handle_camera(data)
		elif data['type'] == 'ground_truth':
			handle_ground_truth(data)
		elif data['type'] == 'command':
			handle_command(data)
		else:
			print(data['type'])

if __name__ == '__main__':
	main()
