from controller.rerouting_controller import ReroutingController
class ForAllFlowsRerouting (ReroutingController):
    def __init__(self, graph_processor):
        super().__init__(graph_processor)