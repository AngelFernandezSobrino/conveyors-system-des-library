class ControllerBase:

    def __init__(self, system_description):
        self.system_description = system_description

    def check_request(self, stopper_id, simulation):
        check_request_function = getattr(self, 'check_request_stopper_' + stopper_id)
        if check_request_function is None:
            return
        check_request_function(simulation)
