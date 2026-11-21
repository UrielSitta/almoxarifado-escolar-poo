# Sistema de Catálogo e Inventário de Almoxarifado Escolar

**Programação Orientada a Objetos I — Partes 2 e 3: Implementação em Python, Testes e Interface Gráfica**  
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

Python 3.10 ou superior. O projeto utiliza bibliotecas padrão do Python, incluindo Tkinter para a interface gráfica.

## Parte 2 — Sistema interativo

Abra um terminal na raiz do projeto e execute:

```
python main.py
```

O `main.py` abre um menu que permite cadastrar e consultar materiais, atualizar quantidades, solicitar materiais, analisar requisições, registrar entregas, fazer inventários e emitir relatórios.

Para encerrar, selecione a opção **0 — Sair**.

## Executar os testes automatizados

```
python -m unittest test_sistema -v
```

Também é possível executar diretamente:

```
python test_sistema.py
```

O arquivo `test_sistema.py` contém **25 testes**, distribuídos entre os módulos de usuários, catálogo, requisições, estoque e a integração com o menu interativo.

Ele verifica as principais regras de negócio:

- **RN1:** nenhuma saída é autorizada quando a quantidade solicitada supera o estoque disponível; o saldo e o histórico de movimentações são preservados.
- **RN2:** materiais desativados não podem ser adicionados a novas requisições; as movimentações antigas são preservadas.

## Parte 3 — Interface Gráfica com Tkinter

Foi desenvolvida uma interface gráfica utilizando a biblioteca Tkinter do Python, permitindo a interação com o sistema por meio de campos de texto, botões e tabelas.

A interface utiliza as classes e os métodos desenvolvidos na Parte 2, mantendo a organização do projeto e os conceitos de Programação Orientada a Objetos.

### Como executar a interface gráfica

Abra um terminal na raiz do projeto e execute:

```
python interface_tk.py
```

A interface possui três abas:

- **Materiais:** permite cadastrar categorias e materiais, visualizar os registros e desativar materiais.
- **Estoque:** permite registrar entradas de materiais e consultar os saldos disponíveis.
- **Requisições:** permite criar solicitações, aprovar ou recusar pedidos e registrar entregas.

As operações realizadas pela interface utilizam os módulos `usuarios.py`, `catalogo.py`, `requisicoes.py` e `estoque.py`.

## Estrutura

```
almoxarifado-escolar-poo/
├── almoxarifado/
│   ├── __init__.py
│   ├── usuarios.py
│   ├── catalogo.py
│   ├── requisicoes.py
│   └── estoque.py
├── main.py
├── interface_tk.py
├── test_sistema.py
└── README.md
```

## Observações

Trata-se de um protótipo acadêmico desenvolvido para aplicar conceitos de Programação Orientada a Objetos, como encapsulamento, abstração, herança e polimorfismo.

O sistema pode ser utilizado pelo menu interativo do terminal ou pela interface gráfica Tkinter.

Os dados são mantidos **somente em memória**: os cadastros e movimentações são perdidos quando o programa é encerrado. O projeto não utiliza banco de dados.
