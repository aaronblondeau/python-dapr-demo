from pydantic import BaseModel
import datetime

# Pydantic class describing a banner
class Banner(BaseModel):
    id: str = ''
    expires: datetime.datetime = datetime.datetime.min
    message: str = ''

# Users can only update the banner message
class UpdateBanner(BaseModel):
    message: str = ''
