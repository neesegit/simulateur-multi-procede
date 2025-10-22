from datetime import datetime, timedelta

class OrchestratorState:
    def __init__(self, start_time: datetime, end_time: datetime, timestep_hours: float) -> None:
        self.start_time = start_time
        self.end_time = end_time
        self.timestep = timestep_hours
        self.current_time = start_time
        self.current_step = 0

    def advance(self):
        """Passe au pas de temps suivant"""
        self.current_time += timedelta(hours=self.timestep)
        self.current_step += 1

    @property
    def total_steps(self) -> int:
        return int((self.end_time - self.start_time).total_seconds() / 3600 / self.timestep)

    def progress_percent(self) -> float:
        return (self.current_step / self.total_steps) * 100