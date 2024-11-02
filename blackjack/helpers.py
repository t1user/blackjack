from functools import wraps
from typing import Callable, Self, TypeVar

T = TypeVar("T")


class PubSubDecorator:
    """
    Instances of this class can be used to decorate functions/methods. Whenever
    decorated function/method is called subscribers will be called with the result
    of the function/method.
    """

    def __init__(self, callables: list[Callable] | None = None):
        if callables is None:
            self.callables = []
        else:
            self.callables = callables

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            return_value = func(*args, **kwargs)
            self.publish(return_value)
            return return_value

        return wrapper

    def subscribe(self, callable) -> None:
        self.callables.append(callable)

    def unsubscribe(self, callable) -> None:
        self.callables.remove(callable)

    def publish(self, *args, **kwargs) -> None:
        for callable in self.callables:
            callable(*args, **kwargs)

    def __iadd__(self, other) -> Self:
        if callable(other):
            self.subscribe(other)
            return self
        else:
            raise NotImplementedError(
                f"Cannot subscribe to {other} of type: {type(other)}"
            )

    def __isub__(self, other) -> Self:
        if callable(other):
            self.unsubscribe(other)
            return self
        else:
            raise NotImplementedError(
                f"Cannot subscribe to {other} of type: {type(other)}"
            )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
