from pydantic import BaseModel
from datetime import datetime

class CreditCardDataModel(BaseModel):
    id: float
    safra_abertura: str
    celular: str
    cidade: str
    estado: str
    idade: str
    sexo: str
    limite_total: float
    limite_disp: float
    data: datetime
    valor: float
    grupo_estabelecimento: str
    cidade_estabelecimento: str
    pais_estabelecimento: str