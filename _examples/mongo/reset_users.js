db.users.deleteMany({});
db.users.insertMany(
	[
		{
			"facility_id" : ObjectId("6162c265089535c20545116d"),
			"name" : "Louis",
			"can_manage_users" : true,
			"can_control_drone" : true
		},
		{
			"facility_id" : ObjectId("6162c265089535c20545116d"),
			"name" : "Laura",
			"can_manage_users" : true,
			"can_control_drone" : true
		},
		{
			"facility_id" : ObjectId("6162c26c089535c20545116e"),
			"name" : "Dennis",
			"can_manage_users" : true,
			"can_control_drone" : true
		},
		{
			"facility_id" : ObjectId("6162c26c089535c20545116e"),
			"name" : "Dorothea",
			"can_manage_users" : true,
			"can_control_drone" : true
		},
		{
			"facility_id" : ObjectId("61631a905c62c1f3e9a38df2"),
			"name" : "Clemens",
			"can_manage_users" : true,
			"can_control_drone" : true
		},
		{
			"facility_id" : ObjectId("61631a905c62c1f3e9a38df2"),
			"name" : "Charlotte",
			"can_manage_users" : true,
			"can_control_drone" : true
		},
	]
);
