# API de Gestão de Loja - Documentação

## Descrição

Este projeto é uma API RESTful desenvolvida com FastAPI para gestão de loja, oferecendo recursos para autenticação de usuários, cadastro e manutenção de produtos, registro de vendas e controle financeiro.

## Funcionalidades

- ✅ Autenticação de Usuários: Cadastro e login com JWT
- ✅ Gestão de Produtos: CRUD completo (Criar, Listar, Atualizar, Deletar)
- ✅ Sistema de Vendas: Registro de vendas com múltiplos itens
- ✅ Controle de Estoque: Atualização automática após vendas
- ✅ Movimentação de Caixa: Controle de entradas e saídas financeiras
- ✅ Gestão de Perfil: Visualização e atualização de dados do usuário

## Libs

- Python 3.9+
- FastAPI
- Supabase: Banco de dados PostgreSQL hospedado
- Pydantic: Validação de dados
- JWT: Autenticação via tokens
- Uvicorn: Servidor ASGI para Python

## Requisitos

- Python 3.9 ou superior
- Conta no Supabase (gratuita ou paga)
- pip (gerenciador de pacotes do Python)

## Executando a API

```
uvicorn main:app --reload
```

## Estrutura do Banco de Dados

- **Usuario**: Armazena dados de usuários e credenciais
- **Produto**: Catálogo de produtos com estoque
- **Venda**: Registro de vendas com valor total
- **ItemVenda**: Itens individuais de cada venda
- **MovimentacaoCaixa**: Controle financeiro de entradas e saídas
  <<<<<<< HEAD

## Prisma

Esse repositório contem o [schema.prisma](schema.prisma) porque o banco de dados foi modelado através dele em um projeto anterior. É apenas uma referência.
