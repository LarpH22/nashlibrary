from dataclasses import dataclass
from datetime import datetime


@dataclass
class Fine:
    loan_id: int
    amount: float
    paid: bool = False
    created_at: datetime | None = None
    fine_id: int | None = None
