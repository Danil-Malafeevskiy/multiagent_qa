from dataclasses import dataclass

from .cart import Cart


@dataclass(frozen=True)
class Order:
    total: float

    def __post_init__(self) -> None:
        if self.total < 0:
            raise ValueError("Order total must be non-negative")


def create_order(cart: Cart) -> Order:
    if cart.is_empty():
        raise ValueError("Cannot create an order from an empty cart")
    return Order(total=cart.total())
