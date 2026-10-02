from pydantic import BaseModel, Field, ConfigDict

class TagPublic(BaseModel):
    id: int
    name: str = Field(..., min_length=1, max_length=30, description="El nombre de la etiqueta (entre 1 y 30 caracteres)", example="Python")
    
    model_config = ConfigDict(from_attributes=True)
    
class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=30, description="El nombre de la etiqueta (entre 1 y 30 caracteres)", example="Python")
    
class TagUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=30, description="El nombre de la etiqueta (entre 1 y 30 caracteres)", example="Python")
    
class TagWithCount(TagPublic):
    uses: int = Field(..., description="Número de posts asociados a la etiqueta")