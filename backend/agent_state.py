class AgentState:

    def __init__(self, question):

        self.question = question

        # Evidence collected from different sources
        self.graph_evidence = {}
        self.vector_evidence = []

        # Agent investigation history
        self.actions_taken = []

        # Agent reasoning state
        self.confidence = 0.0
        self.missing_information = []

        # Final result
        self.final_answer = None

        # Safety limits
        self.max_actions = 5
        self.stopped = False

        # What the agent believes the question requires
        self.required_information = []

        # Evidence evaluation
        self.evidence_agrees = False
        self.evidence_evaluated = False

    def record_action(self, action):

        self.actions_taken.append(action)

    def add_missing_information(self, information):

        if information not in self.missing_information:
            self.missing_information.append(information)

    def remove_missing_information(self, information):

        if information in self.missing_information:
            self.missing_information.remove(information)

    def set_required_information(self, information):

        if information not in self.required_information:
            self.required_information.append(information)

    def update_confidence(self, confidence):

        self.confidence = max(
            0.0,
            min(1.0, confidence)
        )

    def has_action(self, action):

        return action in self.actions_taken

    def should_stop(self, confidence_threshold=0.75):

        # Stop when the agent has enough confidence
        if (
            self.evidence_evaluated
            and self.confidence >= confidence_threshold
        ):
            return True

        # Safety limit
        if len(self.actions_taken) >= self.max_actions:
            return True

        return False