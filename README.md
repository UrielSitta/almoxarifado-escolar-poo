# Sistema de Catálogo e Inventário de Almoxarifado Escolar

**Programação Orientada a Objetos I — Parte 2: Implementação em Python e Testes**  
Instituto Federal Catarinense — Campus Concórdia

Projeto desenvolvido para representar o funcionamento de um almoxarifado escolar, com cadastro de materiais, perfis de usuários, requisições, movimentações de estoque e inventários físicos.

## Como executar

É necessário **Python 3.10 ou superior**. Não são utilizadas bibliotecas externas.

```bash
python main.py
```

Para executar os testes:

```bash
python -m unittest discover -s tests -v
```

## Estrutura

```text
README.md
main.py
almoxarifado/
  __init__.py
  usuarios.py
  catalogo.py
  requisicoes.py
  estoque.py
tests/
  __init__.py
  test_usuarios.py
  test_catalogo.py
  test_requisicoes.py
  test_estoque.py
  test_integracao.py
```

## Modelagem e regras do sistema

- **Abstração, herança e polimorfismo:** `Usuario` é uma classe abstrata; `Administrador`, `Almoxarife` e `Servidor` a especializam e implementam `permissoes()`.
- **Encapsulamento:** atributos internos são protegidos, com acesso e alterações controlados por métodos e propriedades.
- **Requisições:** os pedidos podem ser aprovados, recusados e atendidos parcialmente.
- **Regra 1:** nenhuma saída pode exceder a quantidade disponível, e a movimentação deve ser registrada.
- **Regra 2:** materiais desativados não podem ser incluídos em novas solicitações, mas seu histórico é preservado.
- **Permissões:** aprovação/recusa, movimentações e ajustes de inventário exigem o perfil de almoxarife nos fluxos implementados.

A execução de `main.py` demonstra a interação entre os módulos. O projeto é um protótipo acadêmico com dados em memória; não possui interface gráfica, banco de dados ou autenticação de sessão.
