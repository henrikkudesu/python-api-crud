from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr

class UsuarioBase(BaseModel):
    nome: str
    email: EmailStr

class UsuarioCreate(UsuarioBase):
    senha: str

class Usuario(UsuarioBase):
    id: str
    criadoEm: datetime

    class Config:
        from_attributes = True

class UsuarioUpdateSenha(BaseModel):
    senha_atual: str
    nova_senha: str

class UsuarioProfile(BaseModel):
    nome: str
    email: EmailStr

class ProdutoBase(BaseModel):
    nome: str
    marca: Optional[str] = None
    tipo: Optional[str] = None
    tamanho: Optional[str] = None
    preco: float
    quantidadeEstoque: int

class ProdutoCreate(ProdutoBase):
    pass

class Produto(ProdutoBase):
    id: int
    criadoEm: datetime

    class Config:
        from_attributes = True

class ItemVendaBase(BaseModel):
    produtoId: int
    quantidade: int
    precoUnitario: float

class ItemVendaCreate(ItemVendaBase):
    pass

class ItemVenda(ItemVendaBase):
    id: int
    vendaId: int

    class Config:
        from_attributes = True

class VendaCreate(BaseModel):
    formaPagamento: Optional[str] = None
    itens: List[ItemVendaCreate]

class Venda(BaseModel):
    id: int
    dataVenda: datetime
    total: float
    formaPagamento: Optional[str] = None
    itens: Optional[List[ItemVenda]] = None

    class Config:
        from_attributes = True

class MovimentacaoCaixaBase(BaseModel):
    tipo: str  # "entrada" ou "saída"
    valor: float
    descricao: str
    categoria: Optional[str] = None

class MovimentacaoCaixaCreate(MovimentacaoCaixaBase):
    pass

class MovimentacaoCaixa(MovimentacaoCaixaBase):
    id: int
    data: datetime

    class Config:
        from_attributes = True