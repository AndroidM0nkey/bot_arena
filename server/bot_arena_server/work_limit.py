class WorkLimit:
    def __init__(self, units: int) -> None:
        self.units = units

    def counter(self) -> 'WorkLimitCounter':
        return WorkLimitCounter(self.units)


class WorkLimitCounter:
    def __init__(self, units: int) -> None:
        self.remaining_units = units

    def do_work(self, work_units: int = 1) -> None:
        self.remaining_units -= work_units
        if self.remaining_units < 0:
            raise WorkLimitExceededError()


class WorkLimitExceededError(Exception):
    def __str__(self) -> str:
        return 'Work limit exceeded'
