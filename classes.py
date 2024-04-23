class Timer:
    def __init__(self, tc_type: str = 'fischer', base: int = 300000, inc: int = 10000, period_moves: int = 40) -> None:
        """Manages time control.

        Args:
          tc_type: time control type ['fischer, delay, classical']
          base: base time in ms
          inc: increment time in ms can be negative and 0
          period_moves: number of moves in a period
        """
        self.tc_type = tc_type  # ['fischer', 'delay', 'timepermove']
        self.base = base
        self.inc = inc
        self.period_moves = period_moves
        self.elapse = 0
        self.init_base_time = self.base

    def update_base(self) -> None:
        """Updates base time after every move."""
        if self.tc_type == 'delay':
            self.base += min(0, self.inc - self.elapse)
        elif self.tc_type == 'fischer':
            self.base += self.inc - self.elapse
        elif self.tc_type == 'timepermove':
            self.base = self.init_base_time
        else:
            self.base -= self.elapse

        self.base = max(0, self.base)
        self.elapse = 0
