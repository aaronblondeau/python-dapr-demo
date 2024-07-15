from pydantic import BaseModel

class Banner(BaseModel):
    id: str = ''
    icon: str = ''
    message: str = ''

class UpdateBanner(BaseModel):
    icon: str = ''
    message: str = ''
