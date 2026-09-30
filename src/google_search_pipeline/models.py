from pydantic import BaseModel, ConfigDict

class Model(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    place_id: str
    name: str
    type: str
    website: str | None = None
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    country_code: str | None = None
    rating: float | None = None