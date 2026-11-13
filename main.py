from almoxarifado.catalogo import Categoria, Material, Catalogo
from almoxarifado.usuarios import Administrador, Almoxarife, Servidor, CadastroUsuarios
from almoxarifado.requisicoes import GerenciadorRequisicoes
from almoxarifado.estoque import GestorEstoque


def demonstrar() -> None:
    print("=" * 67)
    print("  SISTEMA DE CATÁLOGO E INVENTÁRIO DE ALMOXARIFADO ESCOLAR")
    print("=" * 67)

    # PARTE 1: usuários, herança, encapsulamento e polimorfismo
    admin = Administrador(1, "Daniel", "admin@escola.edu.br", "senha123")
    almoxarife = Almoxarife(2, "Responsável", "almox@escola.edu.br", "senha123", "MAT-002")
    servidor = Servidor(3, "Professora Ana", "ana@escola.edu.br", "senha123", "Ensino")
    usuarios = CadastroUsuarios()
    for usuario in (admin, almoxarife, servidor):
        admin.gerenciarUsuarios(usuarios, "cadastrar", usuario=usuario)
        print(f"[USUÁRIO] {type(usuario).__name__} {usuario.nome}: {usuario.permissoes()[:2]}")
    print(f"[LOGIN] Senha correta? {servidor.autenticar('senha123')}")

    # PARTE 2: CRUD, categorias, materiais e estoque mínimo
    catalogo = Catalogo()
    papel = Categoria(1, "Papelaria", "Materiais de consumo pedagógico")
    catalogo.cadastrarCategoria(papel)
    caneta = Material(1, "MAT001", "Caneta azul", "unidade", 15, papel)
    caderno = Material(2, "MAT002", "Caderno", "unidade", 5, papel)
    for material in (caneta, caderno):
        almoxarife.cadastrarMaterial(catalogo, material)
    catalogo.atualizarMaterial(2, nome="Caderno universitário")
    print(f"[CATÁLOGO] Materiais ativos: {[m.nome for m in catalogo.listarMateriais()]}")

    # PARTE 4: criar um estoque por material e registrar entradas auditáveis
    gestor = GestorEstoque()
    gestor.registrarEstoque(caneta, "Prateleira A1")
    gestor.registrarEstoque(caderno, "Prateleira B2")
    almoxarife.registrarMovimentacao(gestor, caneta, 20)
    almoxarife.registrarMovimentacao(gestor, caderno, 8)
    print(f"[ESTOQUE] Canetas disponíveis: {gestor.consultarEstoque(caneta).quantidadeAtual}")

    # PARTE 3: requisições, análise e atendimento de forma parcial
    pedidos = GerenciadorRequisicoes(catalogo)
    req = servidor.criarRequisicao(pedidos, 100, [(caneta, 12), (caderno, 3)])
    print(f"[PEDIDO] Requisição {req.id}: {servidor.acompanharRequisicao(pedidos, 100)}")
    almoxarife.analisarRequisicao(pedidos, 100, aprovar=True)
    print(f"[APROVAÇÃO] Novo status: {req.status}")
    gestor.entregar(req, req.itens[0], 6, almoxarife)
    print(f"[ENTREGA PARCIAL] Status: {req.status}; canetas: {gestor.consultarEstoque(caneta).quantidadeAtual}")
    gestor.entregar(req, req.itens[0], 6, almoxarife)
    gestor.entregar(req, req.itens[1], 3, almoxarife)
    print(f"[PEDIDO FINALIZADO] Status: {req.status}")

    # RN1: estoque insuficiente não pode provocar saldo negativo.
    req2 = servidor.criarRequisicao(pedidos, 101, [(caderno, 10)])
    almoxarife.analisarRequisicao(pedidos, 101, aprovar=True)
    saldo_anterior = gestor.consultarEstoque(caderno).quantidadeAtual
    aceito = gestor.entregar(req2, req2.itens[0], 10, almoxarife)
    print(f"[RN1] Entrega sem saldo autorizada? {aceito}; saldo preservado? {saldo_anterior == gestor.consultarEstoque(caderno).quantidadeAtual}")

    # Inventário: comparar contagem e ajustar preservando registro de movimentação.
    inventario = almoxarife.realizarInventario(gestor, 1, [(caneta, 7), (caderno, 5)])
    divergencias = [(i.estoque.material.nome, i.calcularDiferenca()) for i in inventario.apurarDivergencias()]
    print(f"[INVENTÁRIO] Divergências encontradas: {divergencias}")
    ajustes = gestor.ajustarInventario(inventario, almoxarife)
    print(f"[INVENTÁRIO] Ajustes registrados: {len(ajustes)}")

    # RN2: desativação lógica preserva as referências/histórico.
    catalogo.desativarMaterial(caderno.id)
    try:
        servidor.criarRequisicao(pedidos, 102, [(caderno, 1)])
    except ValueError as erro:
        print(f"[RN2] Solicitação de material inativo bloqueada: {erro}")
    print(f"[HISTÓRICO] Movimentações mantidas: {len(gestor.movimentacoes)}")
    print("\n" + admin.emitirRelatorio(gestor))
    print("\nDemonstração concluída.")


if __name__ == "__main__":
    demonstrar()
