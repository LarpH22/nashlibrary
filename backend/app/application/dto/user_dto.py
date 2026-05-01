from dataclasses import dataclass


@dataclass
class UserDTO:
    email: str
    full_name: str
    role: str
    status: str
    student_number: str | None = None
