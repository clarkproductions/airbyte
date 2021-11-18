#
# Copyright (c) 2021 Airbyte, Inc., all rights reserved.
#

import math
from dataclasses import dataclass
from typing import Iterable, List, Tuple

import pendulum
from pendulum.datetime import DateTime, Period


@dataclass
class StreamSlice:
    start_date: DateTime
    end_date: DateTime


class SliceGenerator:

    _start_date: DateTime = None
    _end_data: DateTime = None

    def __init__(self, start_date: DateTime):
        self._start_date = start_date
        self._end_date = pendulum.now("UTC")

    def __iter__(self):
        return self


class RangeSliceGenerator(SliceGenerator):

    RANGE_LENGTH_DAYS: int = 90
    _slices: List[StreamSlice] = []

    def __init__(self, start_date: DateTime):
        super().__init__(start_date)
        self._slices = [
            StreamSlice(start_date=start, end_date=end)
            for start, end in self.make_datetime_ranges(self._start_date, self._end_date, self.RANGE_LENGTH_DAYS)
        ]

    def __next__(self) -> StreamSlice:
        if not self._slices:
            raise StopIteration()
        return self._slices.pop(0)

    @staticmethod
    def make_datetime_ranges(start: DateTime, end: DateTime, range_days: int) -> Iterable[Tuple[DateTime, DateTime]]:
        """
        Generates list of ranges starting from start up to end date with duration of ranges_days.
        Args:
            start (DateTime): start of the range
            end (DateTime): end of the range
            range_days (int): Number in days to split subranges into.

        Returns:
            List[Tuple[DateTime, DateTime]]: list of tuples with ranges.

            Each tuple contains two daytime variables: first is period start
            and second is period end.
        """
        if start > end:
            return []

        next_start = start
        period = pendulum.Duration(days=range_days)
        while next_start < end:
            next_end = min(next_start + period, end)
            yield next_start, next_end
            next_start = next_end


class AdjustableSliceGenerator(SliceGenerator):

    REQUEST_PER_MINUTE_LIMIT = 4
    INITIAL_RANGE_DAYS: int = 30
    DEFAULT_RANGE_DAYS: int = 90
    MAX_RANGE_DAYS: int = 180
    _current_range: int = INITIAL_RANGE_DAYS

    def __init__(self, start_date: DateTime):
        super().__init__(start_date)

    def adjust_range(self, previous_request_time: Period):
        if previous_request_time.total_minutes() == 0:
            self._current_range = self.DEFAULT_RANGE_DAYS
        else:
            days_per_minute = self._current_range / previous_request_time.total_minutes()
            next_range = math.floor(days_per_minute / self.REQUEST_PER_MINUTE_LIMIT)
            self._current_range = min(next_range or self.DEFAULT_RANGE_DAYS, self.MAX_RANGE_DAYS)

    def reduce_range(self) -> StreamSlice:
        self._current_range = int(max(self._current_range / 2, self.INITIAL_RANGE_DAYS))
        return StreamSlice(start_date=self._start_date, end_date=self._start_date + (pendulum.Duration(days=self._current_range)))

    def __next__(self) -> StreamSlice:
        if self._start_date >= self._end_date:
            raise StopIteration()
        next_start_date = min(self._end_date, self._start_date + pendulum.Duration(days=self._current_range))
        slice = StreamSlice(start_date=self._start_date, end_date=next_start_date)
        self._start_date = next_start_date
        return slice
