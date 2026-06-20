from dataclasses import dataclass


@dataclass(frozen=True)
class PromoCode:
    code: str
    discount_percent: float
    is_active: bool

    def __post_init__(self) -> None:
        if not 0 <= self.discount_percent <= 100:
            raise ValueError("Discount percent must be between 0 and 100")


def apply_promo_code(cart_total: float, promo: PromoCode) -> float:
    if cart_total < 0:
        raise ValueError("Cart total must be non-negative")
    if not promo.is_active:
        return cart_total
    discounted_total = cart_total * (1 - promo.discount_percent / 100)
    return max(0.0, discounted_total)
