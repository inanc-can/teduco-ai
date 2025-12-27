"""
Base Pydantic models with automatic camelCase conversion.
"""
from pydantic import BaseModel, ConfigDict
from typing import Any

def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

class CamelCaseModel(BaseModel):
    """
    Base model that automatically converts between snake_case (database) 
    and camelCase (frontend API).
    
    Usage:
        class UserProfile(CamelCaseModel):
            first_name: str
            last_name: str
            current_city: Optional[str] = None
        
        # Database returns: {"first_name": "John", "last_name": "Doe"}
        # API returns: {"firstName": "John", "lastName": "Doe"}
    """
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,  # Allow both snake_case and camelCase input
        from_attributes=True,   # Allow converting from ORM objects
    )
