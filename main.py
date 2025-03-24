from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from database import supabase
from typing import Optional
from models import (
    UsuarioCreate, Usuario, ProdutoCreate, Produto,
    VendaCreate, Venda, ItemVendaCreate, ItemVenda,
    MovimentacaoCaixaCreate, MovimentacaoCaixa, UsuarioUpdateSenha
)
from auth import hash_password, verify_password, create_access_token, decode_token
import uuid

app = FastAPI()

# Configuração de autenticação
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

@app.post("/cadastro")
def cadastrar_usuario(usuario: UsuarioCreate):
    """Rota para cadastro de usuário"""
    try:
        # Hash da senha
        senha_hash = hash_password(usuario.senha)
        
        # Preparar dados para inserção SEM o campo id
        dados_usuario = {
            "nome": usuario.nome,
            "email": usuario.email,
            "senha": senha_hash
        }
        
        # Inserir no Supabase sem o campo id
        response = supabase.table('Usuario').insert(dados_usuario).execute()
        
        return {"mensagem": "Usuário cadastrado com sucesso"}
    except Exception as e:
        print(f"Erro detalhado: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Rota de login"""
    try:
        # Buscar usuário pelo email
        response = supabase.table('Usuario').select('*').eq('email', form_data.username).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou senha incorretos"
            )
        
        usuario = response.data[0]
        
        # Verificar senha
        if not verify_password(form_data.password, usuario['senha']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou senha incorretos"
            )
        
        # Criar token de acesso
        access_token = create_access_token(
            data={"sub": usuario['email']}
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/produtos")
def criar_produto(produto: ProdutoCreate, token: str = Depends(oauth2_scheme)):
    """Rota para criar produto (requer autenticação)"""
    # Validar token
    decode_token(token)
    
    try:
        # Inserir produto no Supabase
        response = supabase.table('Produto').insert(produto.model_dump()).execute()
        
        return {"mensagem": "Produto criado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/produtos")
def listar_produtos(token: str = Depends(oauth2_scheme)):
    """Rota para listar produtos (requer autenticação)"""
    # Validar token
    decode_token(token)
    
    try:
        # Buscar produtos no Supabase
        response = supabase.table('Produto').select('*').execute()
        
        return response.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.get("/produtos/{produto_id}")
def obter_produto(produto_id: int, token: str = Depends(oauth2_scheme)):
    """Rota para obter um produto específico por ID"""
    decode_token(token)
    
    try:
        response = supabase.table('Produto').select('*').eq('id', produto_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
            
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/produtos/{produto_id}")
def atualizar_produto(produto_id: int, produto: ProdutoCreate, token: str = Depends(oauth2_scheme)):
    """Rota para atualizar um produto"""
    decode_token(token)
    
    try:
        # Verificar se o produto existe
        check = supabase.table('Produto').select('id').eq('id', produto_id).execute()
        if not check.data:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        
        # Atualizar produto
        response = supabase.table('Produto').update(produto.model_dump()).eq('id', produto_id).execute()
        
        return {"mensagem": "Produto atualizado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/produtos/{produto_id}")
def deletar_produto(produto_id: int, token: str = Depends(oauth2_scheme)):
    """Rota para deletar um produto"""
    decode_token(token)
    
    try:
        # Verificar se o produto existe
        check = supabase.table('Produto').select('id').eq('id', produto_id).execute()
        if not check.data:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        
        # Deletar produto
        response = supabase.table('Produto').delete().eq('id', produto_id).execute()
        
        return {"mensagem": "Produto deletado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
# Vendas
@app.post("/vendas")
def criar_venda(venda: VendaCreate, token: str = Depends(oauth2_scheme)):
    """Rota para criar uma venda com seus itens"""
    decode_token(token)
    
    try:
        # Calcular o total da venda
        total = 0
        for item in venda.itens:
            total += item.quantidade * item.precoUnitario
        
        # Criar a venda
        dados_venda = {
            "total": total,
            "formaPagamento": venda.formaPagamento
        }
        
        # Inserir venda no Supabase
        venda_response = supabase.table('Venda').insert(dados_venda).execute()
        venda_id = venda_response.data[0]['id']
        
        # Inserir itens da venda
        for item in venda.itens:
            dados_item = {
                "vendaId": venda_id,
                "produtoId": item.produtoId,
                "quantidade": item.quantidade,
                "precoUnitario": item.precoUnitario
            }
            supabase.table('ItemVenda').insert(dados_item).execute()
            
            # Atualizar estoque do produto
            produto = supabase.table('Produto').select('quantidadeEstoque').eq('id', item.produtoId).execute()
            estoque_atual = produto.data[0]['quantidadeEstoque']
            novo_estoque = estoque_atual - item.quantidade
            
            if novo_estoque < 0:
                raise HTTPException(status_code=400, detail=f"Estoque insuficiente para o produto {item.produtoId}")
                
            supabase.table('Produto').update({"quantidadeEstoque": novo_estoque}).eq('id', item.produtoId).execute()
        
        # Registrar movimentação de caixa
        dados_movimentacao = {
            "tipo": "entrada",
            "valor": total,
            "descricao": f"Venda #{venda_id}",
            "categoria": "venda"
        }
        supabase.table('MovimentacaoCaixa').insert(dados_movimentacao).execute()
        
        return {"mensagem": "Venda registrada com sucesso", "vendaId": venda_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/vendas")
def listar_vendas(token: str = Depends(oauth2_scheme)):
    """Rota para listar todas as vendas"""
    decode_token(token)
    
    try:
        response = supabase.table('Venda').select('*').execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/vendas/{venda_id}")
def obter_venda(venda_id: int, token: str = Depends(oauth2_scheme)):
    """Rota para obter detalhes de uma venda específica com seus itens"""
    decode_token(token)
    
    try:
        # Buscar a venda
        venda_response = supabase.table('Venda').select('*').eq('id', venda_id).execute()
        
        if not venda_response.data:
            raise HTTPException(status_code=404, detail="Venda não encontrada")
            
        venda = venda_response.data[0]
        
        # Buscar os itens da venda
        itens_response = supabase.table('ItemVenda').select('*').eq('vendaId', venda_id).execute()
        venda['itens'] = itens_response.data
        
        return venda
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
# Caixa
@app.post("/caixa/movimentacao")
def registrar_movimentacao(movimentacao: MovimentacaoCaixaCreate, token: str = Depends(oauth2_scheme)):
    """Rota para registrar uma movimentação de caixa"""
    decode_token(token)
    
    try:
        response = supabase.table('MovimentacaoCaixa').insert(movimentacao.model_dump()).execute()
        return {"mensagem": "Movimentação registrada com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/caixa/movimentacoes")
def listar_movimentacoes(token: str = Depends(oauth2_scheme), 
                         tipo: Optional[str] = None, 
                         categoria: Optional[str] = None):
    """Rota para listar movimentações do caixa com filtros opcionais"""
    decode_token(token)
    
    try:
        query = supabase.table('MovimentacaoCaixa').select('*')
        
        if tipo:
            query = query.eq('tipo', tipo)
        if categoria:
            query = query.eq('categoria', categoria)
            
        response = query.order('data', desc=True).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/caixa/saldo")
def obter_saldo(token: str = Depends(oauth2_scheme)):
    """Rota para obter o saldo atual do caixa"""
    decode_token(token)
    
    try:
        response = supabase.table('MovimentacaoCaixa').select('*').execute()
        
        saldo = 0
        for mov in response.data:
            if mov['tipo'] == 'entrada':
                saldo += mov['valor']
            else:
                saldo -= mov['valor']
                
        return {"saldo": saldo}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
# User
@app.get("/usuario/perfil")
def obter_perfil(token: str = Depends(oauth2_scheme)):
    """Rota para obter perfil do usuário logado"""
    payload = decode_token(token)
    email = payload.get("sub")
    
    try:
        response = supabase.table('Usuario').select('id,nome,email,criadoEm').eq('email', email).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
            
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/usuario/senha")
def alterar_senha(dados: UsuarioUpdateSenha, token: str = Depends(oauth2_scheme)):
    """Rota para alterar senha do usuário"""
    payload = decode_token(token)
    email = payload.get("sub")
    
    try:
        # Buscar usuário
        response = supabase.table('Usuario').select('*').eq('email', email).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
            
        usuario = response.data[0]
        
        # Verificar senha atual
        if not verify_password(dados.senha_atual, usuario['senha']):
            raise HTTPException(status_code=400, detail="Senha atual incorreta")
            
        # Hash da nova senha
        nova_senha_hash = hash_password(dados.nova_senha)
        
        # Atualizar senha
        supabase.table('Usuario').update({"senha": nova_senha_hash}).eq('id', usuario['id']).execute()
        
        return {"mensagem": "Senha alterada com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))