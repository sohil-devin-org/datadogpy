
from typing import List, Optional  # noqa: F401

from datadog.dogstatsd.metric_types import MetricType


class MetricAggregator:
    def __init__(self,
                 name: str,
                 tags: Optional[List[str]],
                 rate: float,
                 metric_type: str,
                 value: float = 0,
                 timestamp: int = 0,
                 cardinality: Optional[str] = None) -> None:
        self.name = name
        self.tags = tags
        self.rate = rate
        self.metric_type = metric_type
        self.value = value
        self.timestamp = timestamp
        self.cardinality = cardinality

    def aggregate(self, value: float) -> None:
        raise NotImplementedError("Subclasses should implement this method.")


class CountMetric(MetricAggregator):
    def __init__(self,
                 name: str,
                 value: float,
                 tags: Optional[List[str]],
                 rate: float,
                 timestamp: int = 0,
                 cardinality: Optional[str] = None) -> None:
        super().__init__(
            name, tags, rate, MetricType.COUNT, value, timestamp, cardinality
        )

    def aggregate(self, v: float) -> None:
        self.value += v


class GaugeMetric(MetricAggregator):
    def __init__(self,
                 name: str,
                 value: float,
                 tags: Optional[List[str]],
                 rate: float,
                 timestamp: int = 0,
                 cardinality: Optional[str] = None) -> None:
        super().__init__(
            name, tags, rate, MetricType.GAUGE, value, timestamp, cardinality
        )

    def aggregate(self, v: float) -> None:
        self.value = v


class SetMetric(MetricAggregator):
    def __init__(self,
                 name: str,
                 value: float,
                 tags: Optional[List[str]],
                 rate: float,
                 timestamp: int = 0,
                 cardinality: Optional[str] = None) -> None:
        default_value = 0
        super().__init__(
            name, tags, rate, MetricType.SET, default_value, default_value, cardinality
        )
        self.data = set()
        self.data.add(value)

    def aggregate(self, v: float) -> None:
        self.data.add(v)

    def get_data(self) -> List[MetricAggregator]:
        return [
            MetricAggregator(self.name, self.tags, self.rate, MetricType.SET, value)
            for value in self.data
        ]
