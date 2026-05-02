import re
import bleach
from werkzeug.utils import secure_filename
from typing import Optional


class ValidationService:
    """Service for input validation and sanitization"""

    @staticmethod
    def sanitize_text(text: str) -> str:
        """Sanitize text input to prevent XSS attacks"""
        if not text:
            return ""
        # Remove HTML tags and escape special characters
        return bleach.clean(text.strip(), tags=[], strip=True)

    @staticmethod
    def validate_email(email: str) -> tuple[bool, str]:
        """Validate email format and domain restrictions"""
        if not email:
            return False, "Email is required"

        email = email.strip().lower()

        # More strict email regex pattern
        email_pattern = r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'

        if not re.match(email_pattern, email):
            return False, "Invalid email format"

        # Extract domain from email
        email_parts = email.split('@')
        if len(email_parts) != 2:
            return False, "Invalid email format"

        domain = email_parts[1]
        local_part = email_parts[0]

        # Check allowed domains
        allowed_domains = ['gmail.com']
        is_edu_ph_domain = domain.endswith('.edu.ph')

        if not allowed_domains.__contains__(domain) and not is_edu_ph_domain:
            return False, "Only Gmail (gmail.com) and educational domains (.edu.ph) are allowed"

        # Additional validation for educational domains
        if is_edu_ph_domain and len(domain) <= 7:  # ".edu.ph" is 7 chars, so domain must be longer
            return False, "Invalid educational domain format"

        # Basic checks for email deliverability
        if len(local_part) == 0 or len(local_part) > 64:
            return False, "Invalid email local part length"

        if len(domain) == 0 or len(domain) > 253:
            return False, "Invalid email domain length"

        # Check for consecutive dots
        if '..' in local_part or '..' in domain:
            return False, "Email cannot contain consecutive dots"

        # Check for starting/ending with dots
        if local_part.startswith('.') or local_part.endswith('.') or \
           domain.startswith('.') or domain.endswith('.'):
            return False, "Email cannot start or end with dots"

        return True, "Valid email address"

    @staticmethod
    def validate_student_id(student_id: str) -> bool:
        """Validate student ID format (e.g., STU2024001)"""
        if not student_id:
            return False
        # Pattern: STU followed by 4 digits (year) followed by 3+ digits
        pattern = r'^STU\d{4}\d{3,}$'
        return re.match(pattern, student_id.strip()) is not None

    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """
        Validate password strength requirements:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one number
        - At least one special character
        """
        if not password or len(password) < 8:
            return False, "Password must be at least 8 characters long"

        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"

        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"

        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"

        return True, "Password is strong"

    @staticmethod
    def validate_file(file, max_size: int = 5 * 1024 * 1024) -> tuple[bool, str]:
        """Validate uploaded file (type and size)"""
        if not file:
            return False, "No file provided"

        # Check file size
        file.seek(0, 2)  # Seek to end
        size = file.tell()
        file.seek(0)  # Reset to beginning

        if size > max_size:
            return False, f"File size exceeds maximum allowed size of {max_size // (1024*1024)}MB"

        # Check filename
        filename = secure_filename(file.filename)
        if not filename:
            return False, "Invalid filename"

        # Check extension
        allowed_extensions = {'pdf', 'jpg', 'jpeg', 'png'}
        if '.' not in filename or filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            return False, "File type not allowed. Allowed types: PDF, JPG, JPEG, PNG"

        return True, "File is valid"

    @staticmethod
    def validate_required_fields(**fields) -> tuple[bool, str]:
        """Validate that all required fields are provided and not empty"""
        for field_name, value in fields.items():
            if value is None or (isinstance(value, str) and not value.strip()):
                return False, f"{field_name} is required"
        return True, "All required fields are present"
