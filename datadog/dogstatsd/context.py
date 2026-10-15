# Unless explicitly stated otherwise all files in this repository are licensed under the BSD-3-Clause License.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2015-Present Datadog, Inc
# stdlib
from functools import wraps
from inspect import iscoroutinefunction
from time import monotonic
from typing import Any, Callable, List, Optional, Text, TYPE_CHECKING, Union  # noqa: F401

# datadog
from datadog.dogstatsd.context_async import _get_wrapped_co

if TYPE_CHECKING:
    # base.py imports this module, so DogStatsd can only be imported for type checking.
    from datadog.dogstatsd.base import DogStatsd  # noqa: F401


class TimedContextManagerDecorator:
    """
    A context manager and a decorator which will report the elapsed time in
    the context OR in a function call.
    """

    def __init__(
        self,
        statsd: "DogStatsd",
        metric: Optional[Text] = None,
        tags: Optional[List[str]] = None,
        sample_rate: Optional[float] = 1,
        use_ms: Optional[bool] = None,
    ) -> None:
        self.statsd = statsd
        self.timing_func = statsd.timing
        self.metric = metric
        self.tags = tags
        self.sample_rate = sample_rate
        self.use_ms = use_ms
        self.elapsed: Optional[Union[float, int]] = None

    def __call__(
        self, func: Callable[..., Any]
    ) -> Callable[..., Any]:
        """
        Decorator which returns the elapsed time of the function call.

        Default to the function name if metric was not provided.
        """
        if not self.metric:
            self.metric = "%s.%s" % (func.__module__, func.__name__)

        # Coroutines
        if iscoroutinefunction(func):
            return _get_wrapped_co(self, func)

        # Others
        @wraps(func)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            start = monotonic()
            try:
                return func(*args, **kwargs)
            finally:
                self._send(start)

        return wrapped

    def __enter__(self) -> "TimedContextManagerDecorator":
        if not self.metric:
            raise TypeError("Cannot used timed without a metric!")
        self._start = monotonic()
        return self

    def __exit__(self, type: Optional[Any], value: Optional[Any], traceback: Optional[Any]) -> None:
        # Report the elapsed time of the context manager.
        self._send(self._start)

    def _send(
        self,
        start: float,
    ) -> None:
        elapsed = monotonic() - start
        use_ms = self.use_ms if self.use_ms is not None else self.statsd.use_ms
        elapsed = round(1000 * elapsed) if use_ms else elapsed
        self.timing_func(self.metric, elapsed, self.tags, self.sample_rate)  # type: ignore
        self.elapsed = elapsed

    def start(self) -> None:
        self.__enter__()

    def stop(self) -> None:
        self.__exit__(None, None, None)


class DistributedContextManagerDecorator(TimedContextManagerDecorator):
    """
    A context manager and a decorator which will report the elapsed time in
    the context OR in a function call using the custom distribution metric.
    """

    def __init__(
        self,
        statsd: "DogStatsd",
        metric: Optional[Text] = None,
        tags: Optional[List[str]] = None,
        sample_rate: Optional[float] = 1,
        use_ms: Optional[bool] = None,
    ) -> None:
        super().__init__(statsd, metric, tags, sample_rate, use_ms)
        self.timing_func = statsd.distribution
