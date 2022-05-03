class ControllerBase:

    def __init__(self, system_description):
        self.system_description = system_description
        self.external_functions = {}
        self.check_request_functions = {}

    def check_request(self, stopper_id, simulation):
        if stopper_id not in self.check_request_functions:
            return
        self.check_request_functions[stopper_id](simulation)

