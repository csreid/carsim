create table if not exists imu_data (
	frame int not null,
	acc_x float not null,
	acc_y float not null,
	acc_z float not null,
	ang_x float not null,
	ang_y float not null,
	ang_z float not null,
	compass float not null
);

create table if not exists gnss_data (
	frame int not null,
	lat float not null,
	lon float not null,
	alt float not null
);

create table if not exists camera_data (
	frame int not null,
	width int not null,
	height int not null,
	image bytea not null,
	camera_type text not null,
	camera_loc text not null
);

create table if not exists ground_truth(
	frame int not null,
	x float not null,
	y float not null,
	z float not null,
	pitch float not null,
	yaw float not null,
	roll float not null,
	vel_x float not null,
	vel_y float not null,
	vel_z float not null,
	ang_vel_x float not null,
	ang_vel_y float not null,
	ang_vel_z float not null,
	dest_x float not null,
	dest_y float not null,
	dest_z float not null
);

create table if not exists commands (
	frame int not null,
	throttle float not null,
	steer float not null,
	brake float not null
);
