from dataclasses import dataclass
from datetime import datetime


@dataclass
class Student:
    """Student entity with independent authentication"""
    email: str
    full_name: str
    password_hash: str = ''
    student_number: str | None = None
    department: str | None = None
    year_level: int | None = None
    section: str | None = None
    phone: str | None = None
    status: str = 'pending'
    student_id: int | None = None
    email_verified: bool = False
    library_card_number: str | None = None
    expiration_date: str | None = None


@dataclass
class Admin:
    """Admin entity with independent authentication"""
    email: str
    full_name: str
    password_hash: str = ''
    phone: str | None = None
    address: str | None = None
    admin_level: str = 'junior'
    status: str = 'active'
    admin_id: int | None = None
    two_factor_enabled: bool = False
    permissions: dict | None = None


@dataclass
class Librarian:
    """Librarian entity with independent authentication"""
    email: str
    full_name: str
    password_hash: str = ''
    employee_id: str | None = None
    position: str | None = None
    hire_date: str | None = None
    phone: str | None = None
    address: str | None = None
    shift_schedule: str | None = None
    department: str | None = None
    status: str = 'active'
    librarian_id: int | None = None
    permissions: dict | None = None
