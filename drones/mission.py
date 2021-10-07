# Single flight from takeoff to landing on a port
class Mission:
    def __init__(self, start_id, goal_id):
        self.start_id = start_id
        self.goal_id = goal_id

    # generate the object to be sent off to the drone
    def generate(self):
        pass
