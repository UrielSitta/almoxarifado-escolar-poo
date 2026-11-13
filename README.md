# Sistema de Catálogo e Inventário de Almoxarifado Escolar

**Programação Orientada a Objetos I — Parte 2: Implementação em Python e Testes**  
Instituto Federal Catarinense — Campus Concórdia

O projeto simula um almoxarifado escolar com cadastro de categorias e materiais, perfis de usuários, requisições, entradas e saídas de estoque e inventários físicos.

## Integrantes e módulos

| Integrante | Arquivo | Responsabilidade |
|---|---|---|
| Daniel Henrique Petry | `almoxarifado/usuarios.py` | Usuários, permissões, herança e abstração |
| Daniel Murilo Pramio | `almoxarifado/catalogo.py` | Categorias e materiais, CRUD e desativação |
| Uriel Angelo Heckler Sitta | `almoxarifado/requisicoes.py` | Requisições, análise, aprovação e recusa |
| Victor Juan Morche | `almoxarifado/estoque.py` | Estoque, movimentações, entregas e inventário |

## Requisitos

Python 3.10 ou superior. Sem dependências externas.

## Executar o sistema interativo

Abra um terminal na raiz do projeto e execute:

```bash
python main.py
```

O `main.py` abre um menu que permite cadastrar e consultar materiais, atualizar quantidades, solicitar materiais, analisar requisições, registrar entregas, fazer inventários e emitir relatórios. Para encerrar, selecione a opção **0 — Sair**.

## Executar os testes automatizados

```bash
python -m unittest test_sistema -v
```

Também é possível executar diretamente:

```bash
python test_sistema.py
```

O arquivo `test_sistema.py` contém **25 testes**, distribuídos entre os módulos de usuários, catálogo, requisições, estoque e a integração com o menu interativo. Ele verifica as principais regras de negócio:

- **RN1:** nenhuma saída é autorizada quando a quantidade solicitada supera o estoque disponível; o saldo e o histórico de movimentações são preservados.
- **RN2:** materiais desativados não podem ser adicionados a novas requisições; as movimentações antigas são preservadas.

## Estrutura

```text
almoxarifado-escolar-poo/
├── almoxarifado/
│   ├── __init__.py
│   ├── usuarios.py
│   ├── catalogo.py
│   ├── requisicoes.py
│   └── estoque.py
├── main.py
├── test_sistema.py
└── README.md
```

## Observações

Trata-se de um protótipo acadêmico que mantém os dados **somente em memória**: os cadastros e movimentações são perdidos quando o programa é encerrado. Não há banco de dados ou interface gráfica; a interação ocorre no terminal.
