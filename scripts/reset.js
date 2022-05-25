// reset users
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

// Praxis Lorem Ipsum
db.facilities.updateOne(
	{
		"_id": ObjectId("6162c265089535c20545116d")
	},
	{
		"$set": {
			"new_user": {
				"key": "3BN4S97W",
				"expiry": new Date("2023-01-01"),
				"can_manage_users": true,
				"can_control_drone": true
			}
		}
	}
);

// Praxis Dolor Amet
db.facilities.updateOne(
	{
		"_id": ObjectId("6162c26c089535c20545116e")
	},
	{
		"$set": {
			"new_user": {
				"key": "T648SD9S",
				"expiry": new Date("2023-01-01"),
				"can_manage_users": true,
				"can_control_drone": true
			}
		}
	}
);

// Labor Consectetur Elit
db.facilities.updateOne(
	{
		"_id": ObjectId("61631a905c62c1f3e9a38df2")
	},
	{
		"$set": {
			"new_user": {
				"key": "89NESJ5M",
				"expiry": new Date("2023-01-01"),
				"can_manage_users": true,
				"can_control_drone": true
			}
		}
	}
);
