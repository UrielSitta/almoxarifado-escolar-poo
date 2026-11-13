"""Interface interativa de terminal do almoxarifado escolar.

Execute com ``python main.py`` e use o menu até escolher sair.
"""

from almoxarifado.catalogo import Categoria, Material, Catalogo
from almoxarifado.usuarios import Administrador, Almoxarife, Servidor, CadastroUsuarios
from almoxarifado.requisicoes import GerenciadorRequisicoes
from almoxarifado.estoque import GestorEstoque


def ler_texto(pergunta: str) -> str:
    while True:
        resposta = input(pergunta).strip()
        if resposta:
            return resposta
        print("Digite um valor para continuar.")


def ler_numero(pergunta: str, minimo: int = 1) -> int:
    while True:
        try:
            valor = int(ler_texto(pergunta))
            if valor >= minimo:
                return valor
        except ValueError:
            pass
        print(f"Informe um número inteiro maior ou igual a {minimo}.")


def confirmar(pergunta: str) -> bool:
    return ler_texto(pergunta + " [s/n]: ").lower() in ("s", "sim")


class MenuAlmoxarifado:
    def __init__(self) -> None:
        self.admin = Administrador(1, "Administrador", "admin@escola.edu.br", "senha123")
        self.almoxarife = Almoxarife(2, "Almoxarife", "almox@escola.edu.br", "senha123", "ALM-001")
        self.servidor = Servidor(3, "Professora Ana", "ana@escola.edu.br", "senha123", "Ensino")
        self.usuarios = CadastroUsuarios()
        for usuario in (self.admin, self.almoxarife, self.servidor):
            self.admin.gerenciarUsuarios(self.usuarios, "cadastrar", usuario=usuario)
        self.catalogo = Catalogo()
        self.gestor = GestorEstoque()
        self.pedidos = GerenciadorRequisicoes(self.catalogo)
        self.proximo_material = 1
        self.proxima_categoria = 1
        self.proximo_pedido = 1
        self.proximo_inventario = 1
        self.proximo_servidor = 4

    def listar_categorias(self) -> None:
        print("\nCATEGORIAS CADASTRADAS")
        for c in self.catalogo.listarCategorias():
            print(f"  {c.id} - {c.nome} | {c.descricao}")

    def listar_materiais(self) -> None:
        print("\nCATÁLOGO E SALDOS")
        for m in self.catalogo.listarMateriais(incluirInativos=True):
            try:
                estoque = self.gestor.consultarEstoque(m)
                saldo = estoque.quantidadeAtual
            except LookupError:
                saldo = "sem estoque"
            situacao = "ATIVO" if m.ativo else "INATIVO"
            print(f"  ID {m.id} | {m.codigo} | {m.nome} | {situacao} | saldo: {saldo} | mínimo: {m.estoqueMinimo}")

    def cadastrar_categoria(self) -> None:
        nome = ler_texto("Nome da categoria: ")
        descricao = input("Descrição (opcional): ").strip()
        categoria = Categoria(self.proxima_categoria, nome, descricao)
        self.catalogo.cadastrarCategoria(categoria)
        self.proxima_categoria += 1
        print(f"Categoria criada: {categoria.id} - {categoria.nome}")

    def cadastrar_material(self) -> None:
        self.listar_categorias()
        categoria = self.catalogo.consultarCategoria(ler_numero("ID da categoria: "))
        codigo = ler_texto("Código do material: ")
        nome = ler_texto("Nome do material: ")
        unidade = ler_texto("Unidade de medida: ")
        minimo = ler_numero("Estoque mínimo: ", 0)
        local = ler_texto("Localização/prateleira: ")
        material = Material(self.proximo_material, codigo, nome, unidade, minimo, categoria)
        self.almoxarife.cadastrarMaterial(self.catalogo, material)
        self.gestor.registrarEstoque(material, local)
        self.proximo_material += 1
        print(f"Material {material.codigo} cadastrado. Saldo inicial: 0. Use a opção de entrada.")

    def atualizar_material(self) -> None:
        self.listar_materiais()
        material = self.catalogo.consultarMaterial(ler_numero("ID do material a atualizar: "))
        print("Deixe em branco o campo que não deseja alterar.")
        nome = input(f"Nome [{material.nome}]: ").strip()
        unidade = input(f"Unidade [{material.unidade}]: ").strip()
        minimo = input(f"Estoque mínimo [{material.estoqueMinimo}]: ").strip()
        alteracoes = {}
        if nome:
            alteracoes['nome'] = nome
        if unidade:
            alteracoes['unidade'] = unidade
        if minimo:
            try:
                alteracoes['estoqueMinimo'] = int(minimo)
            except ValueError as erro:
                raise ValueError("O estoque mínimo deve ser um número inteiro.") from erro
        if not alteracoes:
            print("Nenhuma alteração informada.")
            return
        self.catalogo.atualizarMaterial(material.id, **alteracoes)
        print("Material atualizado com sucesso.")

    def desativar_material(self) -> None:
        self.listar_materiais()
        material = self.catalogo.consultarMaterial(ler_numero("ID do material a desativar: "))
        if confirmar(f"Desativar {material.nome} sem apagar seu histórico?"):
            print("Material desativado." if self.catalogo.desativarMaterial(material.id) else "Já estava inativo.")

    def registrar_entrada(self) -> None:
        self.listar_materiais()
        material = self.catalogo.consultarMaterial(ler_numero("ID do material: "))
        qtd = ler_numero("Quantidade de entrada: ")
        movimento = self.almoxarife.registrarMovimentacao(self.gestor, material, qtd)
        print(f"Entrada registrada, movimento #{movimento.id}. Saldo: {self.gestor.consultarEstoque(material).quantidadeAtual}")

    def cadastrar_servidor(self) -> None:
        nome = ler_texto("Nome do servidor: ")
        email = ler_texto("E-mail: ")
        setor = ler_texto("Setor: ")
        senha = ler_texto("Senha (mínimo 6 caracteres): ")
        usuario = Servidor(self.proximo_servidor, nome, email, senha, setor)
        self.admin.gerenciarUsuarios(self.usuarios, "cadastrar", usuario=usuario)
        self.proximo_servidor += 1
        print(f"Servidor cadastrado com ID {usuario.id}.")

    def selecionar_servidor(self) -> None:
        print("\nSERVIDORES DISPONÍVEIS")
        servidores = [u for u in self.usuarios.listar() if isinstance(u, Servidor)]
        for u in servidores:
            print(f"  {u.id} - {u.nome} ({u.setor})")
        usuario = self.usuarios.consultar(ler_numero("ID do servidor para fazer pedidos: "))
        if not isinstance(usuario, Servidor):
            raise ValueError("Escolha o ID de um servidor solicitante.")
        self.servidor = usuario
        print(f"Servidor selecionado: {usuario.nome}")

    def criar_pedido(self) -> None:
        print(f"\nSolicitante atual: {self.servidor.nome}")
        self.listar_materiais()
        itens = []
        print("Adicione materiais ao pedido. Digite 0 para finalizar.")
        while True:
            id_material = ler_numero("ID do material (0 para finalizar): ", 0)
            if id_material == 0:
                break
            material = self.catalogo.consultarMaterial(id_material)
            if any(m.id == id_material for m, _ in itens):
                print("Material já incluído neste pedido.")
                continue
            if not material.ativo:
                print("Material inativo não pode ser solicitado.")
                continue
            quantidade = ler_numero(f"Quantidade solicitada de {material.nome}: ")
            itens.append((material, quantidade))
        if not itens:
            print("Pedido cancelado: nenhum material informado.")
            return
        req = self.servidor.criarRequisicao(self.pedidos, self.proximo_pedido, itens)
        self.proximo_pedido += 1
        print(f"Requisição #{req.id} criada. Status: {req.status}")

    def listar_pedidos(self) -> None:
        print("\nREQUISIÇÕES")
        pedidos = self.pedidos.listarRequisicoes()
        if not pedidos:
            print("Nenhuma requisição cadastrada.")
        for req in pedidos:
            print(f"  Pedido #{req.id} | {req.solicitante.nome} | {req.status}")
            for pos, item in enumerate(req.itens, 1):
                print(f"    [{pos}] {item.material.nome}: solicitados={item.quantidadeSolicitada}, "
                      f"entregues={item.quantidadeAtendida}, pendentes={item.saldoPendente()}")

    def analisar_pedido(self) -> None:
        self.listar_pedidos()
        id_pedido = ler_numero("ID da requisição: ")
        decisao = ler_texto("Aprovar ou recusar? [a/r]: ").lower()
        if decisao not in ('a', 'r'):
            print("Informe 'a' para aprovar ou 'r' para recusar.")
            return
        aprovado = self.almoxarife.analisarRequisicao(self.pedidos, id_pedido, aprovar=decisao == 'a')
        print(f"Situação atual: {self.pedidos.consultarRequisicao(id_pedido).status}" if aprovado else "Pedido não está pendente ou não pode ser analisado.")

    def entregar_pedido(self) -> None:
        self.listar_pedidos()
        req = self.pedidos.consultarRequisicao(ler_numero("ID do pedido a entregar: "))
        if req.status not in (req.APROVADA, req.PARCIAL):
            print("Primeiro aprove o pedido. Pedidos recusados ou finalizados não aceitam entregas.")
            return
        pos = ler_numero("Número do item [entre colchetes]: ")
        if pos > len(req.itens):
            print("Número de item inválido.")
            return
        item = req.itens[pos - 1]
        qtd = ler_numero("Quantidade a entregar: ")
        resultado = self.gestor.entregar(req, item, qtd, self.almoxarife)
        if not resultado:
            print("Entrega bloqueada: não existe saldo disponível suficiente (RN1).")
            return
        print(f"Entrega registrada! Pedido #{req.id}: {req.status}. "
              f"Saldo de {item.material.nome}: {self.gestor.consultarEstoque(item.material).quantidadeAtual}")

    def fazer_inventario(self) -> None:
        self.listar_materiais()
        contagens = []
        print("Informe contagens físicas. Digite 0 para finalizar.")
        while True:
            id_material = ler_numero("ID do material a contar (0 para finalizar): ", 0)
            if id_material == 0:
                break
            material = self.catalogo.consultarMaterial(id_material)
            if any(m is material for m, _ in contagens):
                print("Material já contado neste inventário.")
                continue
            self.gestor.consultarEstoque(material)
            atual = self.gestor.consultarEstoque(material).quantidadeAtual
            print(f"Saldo atual do sistema: {atual}")
            qtd = ler_numero("Quantidade contada fisicamente: ", 0)
            contagens.append((material, qtd))
        if not contagens:
            print("Inventário cancelado: nenhuma contagem realizada.")
            return
        inv = self.almoxarife.realizarInventario(self.gestor, self.proximo_inventario, contagens)
        self.proximo_inventario += 1
        print(f"Inventário #{inv.id}: {inv.status}")
        for item in inv.itens:
            print(f"  {item.estoque.material.nome}: sistema={item.quantidadeSistema}, "
                  f"contado={item.quantidadeContada}, diferença={item.calcularDiferenca()}")
        if confirmar("Aplicar ajustes para igualar o saldo às contagens?"):
            movimentos = self.gestor.ajustarInventario(inv, self.almoxarife)
            print(f"Ajuste aplicado. {len(movimentos)} movimentações registradas.")
        else:
            print("Inventário registrado sem ajuste de estoque.")

    def listar_movimentacoes(self) -> None:
        print("\nHISTÓRICO DE MOVIMENTAÇÕES")
        for m in self.gestor.movimentacoes:
            print(f"  #{m.id} | {m.dataHora:%d/%m/%Y %H:%M} | {m.tipo} | "
                  f"{m.estoque.material.nome} | {m.quantidade} | {m.responsavel.nome}")
        if not self.gestor.movimentacoes:
            print("Nenhum movimento.")

    def abaixo_minimo(self) -> None:
        print("\nMATERIAIS ABAIXO DO ESTOQUE MÍNIMO")
        estoques = self.gestor.consultarItensAbaixoMinimo()
        if not estoques:
            print("Nenhum material abaixo do mínimo.")
        for estoque in estoques:
            print(f"  {estoque.material.nome}: {estoque.quantidadeAtual} de mínimo {estoque.material.estoqueMinimo}")

    def mostrar_menu(self) -> None:
        print("\n" + "=" * 60)
        print("     SISTEMA DE ALMOXARIFADO ESCOLAR - MENU")
        print("=" * 60)
        print(" 1 - Listar materiais e saldos       9 - Listar requisições")
        print(" 2 - Cadastrar categoria            10 - Aprovar/recusar pedido")
        print(" 3 - Cadastrar material             11 - Entregar materiais")
        print(" 4 - Atualizar material             12 - Fazer inventário")
        print(" 5 - Desativar material             13 - Histórico de movimentações")
        print(" 6 - Registrar entrada              14 - Relatório completo")
        print(" 7 - Cadastrar servidor             15 - Estoque abaixo do mínimo")
        print(" 8 - Criar requisição               16 - Selecionar servidor")
        print(" 0 - Sair")

    def executar(self) -> None:
        acoes = {
            '1': self.listar_materiais, '2': self.cadastrar_categoria,
            '3': self.cadastrar_material, '4': self.atualizar_material,
            '5': self.desativar_material, '6': self.registrar_entrada,
            '7': self.cadastrar_servidor, '8': self.criar_pedido,
            '9': self.listar_pedidos, '10': self.analisar_pedido,
            '11': self.entregar_pedido, '12': self.fazer_inventario,
            '13': self.listar_movimentacoes,
            '14': lambda: print("\n" + self.admin.emitirRelatorio(self.gestor)),
            '15': self.abaixo_minimo, '16': self.selecionar_servidor,
        }
        print("\nSistema iniciado. Cadastre uma categoria e depois seus materiais.")
        print("As alterações ficam na memória enquanto o programa estiver aberto.")
        print("Ao sair, elas serão perdidas (não há banco de dados).")
        while True:
            try:
                self.mostrar_menu()
                opcao = ler_texto("Escolha uma opção: ")
                if opcao == '0':
                    print("Sistema encerrado.")
                    break
                acao = acoes.get(opcao)
                if acao is None:
                    print("Opção inválida. Escolha um número do menu.")
                    continue
                try:
                    acao()
                except (ValueError, TypeError, LookupError, PermissionError, RuntimeError, KeyError) as erro:
                    print(f"Não foi possível concluir a operação: {erro}")
                input("\nPressione Enter para voltar ao menu...")
            except (EOFError, KeyboardInterrupt):
                print("\nSistema encerrado.")
                break


if __name__ == "__main__":
    MenuAlmoxarifado().executar()
