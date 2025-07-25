from pydantic import BaseModel, EmailStr, model_validator, Field
from typing import List, Optional


class UserRead(BaseModel):
    id: int
    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    is_verified: Optional[bool] = None


class UserInDB(UserRead):
    hashed_password: str


class CafeBase(BaseModel):
    title: str
    city: str
    description: str
    image_url: Optional[str] = None


class CafeCreate(CafeBase):
    best_for: str
    also_good_for: List[str]


class CafeResponse(CafeBase):
    id: int
    best_for: Optional[str]
    also_good_for: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True

    @model_validator(mode='before')
    @classmethod
    def transform_category_objects_to_names(cls, data):
        if not isinstance(data, dict):
            processed_data = {
                'id': getattr(data, 'id', None),
                'title': getattr(data, 'title', None),
                'city': getattr(data, 'city', None),
                'description': getattr(data, 'description', None),
                'image_url': getattr(data, 'image_url', None),
            }
            best_for_category_obj = getattr(data, 'best_for_category', None)
            category_associations = getattr(data, 'category_associations', None)

        else:
            processed_data = data
            best_for_category_obj = data.get('best_for_category', None)
            category_associations = data.get('category_associations', None)

        if isinstance(processed_data.get('best_for'), str):
            processed_data['best_for'] = processed_data['best_for']
        elif best_for_category_obj is not None and hasattr(best_for_category_obj, 'name'):
            processed_data['best_for'] = best_for_category_obj.name
        elif category_associations is not None:
            found_best_for_name = None
            for assoc in category_associations:
                if getattr(assoc, 'is_best', False) and getattr(assoc, 'category', None) is not None and hasattr(
                        assoc.category, 'name'):
                    found_best_for_name = assoc.category.name
                    break
            processed_data['best_for'] = found_best_for_name
        else:
            processed_data['best_for'] = None

        also_good_for_names = []
        if category_associations is not None:
            for assoc in category_associations:
                if not getattr(assoc, 'is_best', True) and getattr(assoc, 'category', None) is not None and hasattr(
                        assoc.category, 'name'):
                    also_good_for_names.append(assoc.category.name)
        processed_data['also_good_for'] = also_good_for_names

        return processed_data
