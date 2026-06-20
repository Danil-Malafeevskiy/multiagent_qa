from dataclasses import dataclass, field


@dataclass(frozen=True)
class CartItem:
    name: str
    price: float
    quantity: int

    def __post_init__(self) -> None:
        if self.price < 0:
            raise ValueError("Item price must be non-negative")
        if self.quantity <= 0:
            raise ValueError("Item quantity must be positive")


@dataclass
class Cart:
    items: list[CartItem] = field(default_factory=list)

    def add_item(self, item: CartItem) -> None:
        self.items.append(item)

    def total(self) -> float:
        return sum(item.price * item.quantity for item in self.items)

    def is_empty(self) -> bool:
        return not self.items
