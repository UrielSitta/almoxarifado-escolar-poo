"""Testes automatizados do Sistema de Almoxarifado Escolar.

Execute: python -m unittest test_sistema -v
"""

import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from almoxarifado.catalogo import Categoria, Catalogo, Material
from almoxarifado.estoque import GestorEstoque
from almoxarifado.requisicoes import GerenciadorRequisicoes, Requisicao
from almoxarifado.usuarios import Usuario, Administrador, Almoxarife, Servidor, CadastroUsuarios
from main import MenuAlmoxarifado


# Test Usuarios
class TestUsuarios(unittest.TestCase):
    def setUp(self):
        self.admin = Administrador(1, "Ana", "ana@escola.edu.br", "abc123")
        self.almox = Almoxarife(2, "Bruno", "bruno@escola.edu.br", "abc123", "A02")
        self.servidor = Servidor(3, "Carla", "carla@escola.edu.br", "abc123", "Ensino")

    def test_abstracao_e_polimorfismo(self):
        with self.assertRaises(TypeError):
            Usuario(5, "Abstrato", "teste@escola.edu.br", "abc123")
        usuarios = [self.admin, self.almox, self.servidor]
        self.assertTrue(all(isinstance(u, Usuario) for u in usuarios))
        self.assertNotEqual(self.admin.permissoes(), self.almox.permissoes())
        self.assertNotEqual(self.almox.permissoes(), self.servidor.permissoes())

    def test_autenticacao_e_senha_protegida(self):
        self.assertTrue(self.servidor.autenticar("abc123"))
        self.assertFalse(self.servidor.autenticar("errada"))
        self.assertNotIn("abc123", repr(self.servidor))
        with self.assertRaises(AttributeError):
            _ = self.servidor.senhaHash

    def test_gerenciamento_de_usuarios(self):
        cadastro = CadastroUsuarios()
        self.admin.gerenciarUsuarios(cadastro, "cadastrar", usuario=self.servidor)
        self.assertIs(cadastro.consultar(3), self.servidor)
        self.admin.gerenciarUsuarios(cadastro, "atualizar", id=3, nome="Carla Silva")
        self.assertEqual(self.servidor.nome, "Carla Silva")
        self.assertIs(self.admin.gerenciarUsuarios(cadastro, "excluir", id=3), self.servidor)
        self.assertEqual(cadastro.listar(), [])

    def test_email_unico(self):
        cadastro = CadastroUsuarios()
        cadastro.cadastrar(self.admin)
        with self.assertRaises(ValueError):
            cadastro.cadastrar(Servidor(4, "Outra", "ana@escola.edu.br", "abc123", "Secretaria"))


# Test Catalogo
class TestCatalogo(unittest.TestCase):
    def setUp(self):
        self.catalogo = Catalogo()
        self.categoria = Categoria(1, "Papelaria", "Materiais escolares")
        self.catalogo.cadastrarCategoria(self.categoria)
        self.material = Material(10, "P01", "Papel sulfite", "resma", 5, self.categoria)
        self.catalogo.cadastrarMaterial(self.material)

    def test_crud_material(self):
        self.assertIs(self.catalogo.consultarMaterial(10), self.material)
        self.assertEqual(self.catalogo.buscarPorCodigo("p01").nome, "Papel sulfite")
        self.catalogo.atualizarMaterial(10, nome="Papel A4", estoqueMinimo=10)
        self.assertEqual(self.material.nome, "Papel A4")
        self.assertEqual(self.material.estoqueMinimo, 10)
        self.assertTrue(self.catalogo.desativarMaterial(10))
        self.assertEqual(self.catalogo.listarMateriais(), [])
        self.assertEqual(self.catalogo.listarMateriais(incluirInativos=True), [self.material])
        self.assertFalse(self.catalogo.desativarMaterial(10))

    def test_codigo_nao_pode_ser_reutilizado(self):
        self.catalogo.desativarMaterial(10)
        outro = Material(11, "P01", "Outro produto", "unidade", 0, self.categoria)
        with self.assertRaises(ValueError):
            self.catalogo.cadastrarMaterial(outro)

    def test_integridade_das_categorias(self):
        with self.assertRaises(ValueError):
            self.catalogo.desativarCategoria(1)
        self.catalogo.desativarMaterial(10)
        self.catalogo.desativarCategoria(1)
        self.assertEqual(self.catalogo.listarCategorias(), [])
        self.assertEqual(len(self.catalogo.listarCategorias(incluirInativas=True)), 1)

    def test_atualizacao_que_falha_nao_altera_o_nome(self):
        with self.assertRaises(ValueError):
            self.catalogo.atualizarMaterial(10, nome="Nome Novo", estoqueMinimo=-1)
        self.assertEqual(self.material.nome, "Papel sulfite")


# Test Requisicoes
class TestRequisicoes(unittest.TestCase):
    def setUp(self):
        self.catalogo = Catalogo()
        cat = Categoria(1, "Papelaria")
        self.catalogo.cadastrarCategoria(cat)
        self.material = Material(1, "L01", "Lápis", "unidade", 2, cat)
        self.catalogo.cadastrarMaterial(self.material)
        self.servidor = Servidor(1, "Solicitante", "sol@escola.edu.br", "abc123", "Ensino")
        self.outra = Servidor(2, "Outro", "outro@escola.edu.br", "abc123", "Ensino")
        self.almox = Almoxarife(3, "Almoxarife", "almox@escola.edu.br", "abc123", "A03")
        self.gerenciador = GerenciadorRequisicoes(self.catalogo)

    def test_criar_aprovar_e_acompanhar(self):
        req = self.servidor.criarRequisicao(self.gerenciador, 10, [(self.material, 3)])
        self.assertEqual(req.status, Requisicao.PENDENTE)
        self.assertEqual(req.itens[0].saldoPendente(), 3)
        self.assertTrue(self.almox.analisarRequisicao(self.gerenciador, 10, aprovar=True))
        self.assertEqual(self.servidor.acompanharRequisicao(self.gerenciador, 10), Requisicao.APROVADA)
        with self.assertRaises(PermissionError):
            self.outra.acompanharRequisicao(self.gerenciador, 10)

    def test_recusar_nao_permita_aprovar_de_novo(self):
        req = self.servidor.criarRequisicao(self.gerenciador, 20, [(self.material, 1)])
        self.assertTrue(self.almox.analisarRequisicao(self.gerenciador, 20, aprovar=False))
        self.assertEqual(req.status, Requisicao.RECUSADA)
        self.assertFalse(self.almox.analisarRequisicao(self.gerenciador, 20, aprovar=True))

    def test_aprovacao_direta_sem_almoxarife_e_bloqueada(self):
        req = self.servidor.criarRequisicao(self.gerenciador, 21, [(self.material, 2)])
        for responsavel in (None, self.servidor, object()):
            with self.subTest(responsavel=responsavel):
                with self.assertRaises(PermissionError):
                    req.aprovar(responsavel)
                self.assertEqual(req.status, Requisicao.PENDENTE)
                self.assertIsNone(req.almoxarife)

    def test_recusa_direta_sem_almoxarife_e_bloqueada(self):
        req = self.servidor.criarRequisicao(self.gerenciador, 22, [(self.material, 2)])
        for responsavel in (None, self.servidor):
            with self.subTest(responsavel=responsavel):
                with self.assertRaises(PermissionError):
                    req.recusar(responsavel)
                self.assertEqual(req.status, Requisicao.PENDENTE)

    def test_gerenciador_bloqueia_papel_incorreto(self):
        req = self.servidor.criarRequisicao(self.gerenciador, 23, [(self.material, 2)])
        with self.assertRaises(PermissionError):
            self.gerenciador.analisarRequisicao(23, self.servidor, True)
        with self.assertRaises(PermissionError):
            self.gerenciador.criarRequisicao(24, self.almox, [(self.material, 1)])
        with self.assertRaises(PermissionError):
            Requisicao(24, self.almox)
        self.assertEqual(req.status, Requisicao.PENDENTE)
        self.assertEqual(len(self.gerenciador.listarRequisicoes()), 1)

    def test_material_inativo_nao_pode_ser_solicitado(self):
        self.catalogo.desativarMaterial(1)
        with self.assertRaises(ValueError):
            self.servidor.criarRequisicao(self.gerenciador, 30, [(self.material, 1)])
        self.assertEqual(self.gerenciador.listarRequisicoes(), [])

    def test_requisicao_sem_itens_ou_duplicados(self):
        with self.assertRaises(ValueError):
            self.servidor.criarRequisicao(self.gerenciador, 40, [])
        with self.assertRaises(ValueError):
            self.servidor.criarRequisicao(self.gerenciador, 40, [(self.material, 1), (self.material, 2)])
        self.assertEqual(self.gerenciador.listarRequisicoes(), [])


# Test Estoque
class TestEstoque(unittest.TestCase):
    def setUp(self):
        self.catalogo = Catalogo()
        categoria = Categoria(1, "Consumo")
        self.catalogo.cadastrarCategoria(categoria)
        self.material = Material(1, "M01", "Caneta", "unidade", 3, categoria)
        self.catalogo.cadastrarMaterial(self.material)
        self.almox = Almoxarife(1, "Almox", "almox@escola.edu.br", "abc123", "A01")
        self.servidor = Servidor(2, "Serv", "serv@escola.edu.br", "abc123", "Ensino")
        self.gestor = GestorEstoque()
        self.estoque = self.gestor.registrarEstoque(self.material, "A1")
        self.pedidos = GerenciadorRequisicoes(self.catalogo)

    def test_entrada_e_alerta_de_minimo(self):
        self.assertEqual(self.gestor.consultarItensAbaixoMinimo(), [self.estoque])
        movimento = self.gestor.registrarEntrada(self.material, 10, self.almox)
        self.assertEqual(self.estoque.quantidadeAtual, 10)
        self.assertEqual(movimento.tipo, "ENTRADA")
        self.assertFalse(self.estoque.abaixoDoMinimo())

    def test_rn1_saida_nao_pode_ultrapassar_saldo(self):
        self.gestor.registrarEntrada(self.material, 4, self.almox)
        req = self.servidor.criarRequisicao(self.pedidos, 1, [(self.material, 5)])
        self.almox.analisarRequisicao(self.pedidos, 1, aprovar=True)
        qtd_movs = len(self.gestor.movimentacoes)
        self.assertFalse(self.gestor.entregar(req, req.itens[0], 5, self.almox))
        self.assertEqual(self.estoque.quantidadeAtual, 4)
        self.assertEqual(req.status, Requisicao.APROVADA)
        self.assertEqual(len(self.gestor.movimentacoes), qtd_movs)

    def test_entrega_parcial_e_conclusao(self):
        self.gestor.registrarEntrada(self.material, 10, self.almox)
        req = self.servidor.criarRequisicao(self.pedidos, 2, [(self.material, 7)])
        with self.assertRaises(ValueError):
            self.gestor.entregar(req, req.itens[0], 2, self.almox)
        self.almox.analisarRequisicao(self.pedidos, 2, aprovar=True)
        self.assertTrue(self.gestor.entregar(req, req.itens[0], 2, self.almox))
        self.assertEqual(req.status, Requisicao.PARCIAL)
        self.assertEqual(self.estoque.quantidadeAtual, 8)
        self.assertTrue(self.gestor.entregar(req, req.itens[0], 5, self.almox))
        self.assertEqual(req.status, Requisicao.ATENDIDA)
        self.assertEqual(self.estoque.quantidadeAtual, 3)
        saidas = [mov for mov in self.gestor.movimentacoes if mov.tipo == "SAIDA"]
        self.assertEqual([mov.quantidade for mov in saidas], [2, 5])
        self.assertTrue(all(mov.itemRequisicao is req.itens[0] for mov in saidas))

    def test_entrega_por_servidor_nao_muda_saldo_nem_requisicao(self):
        self.gestor.registrarEntrada(self.material, 7, self.almox)
        req = self.servidor.criarRequisicao(self.pedidos, 31, [(self.material, 4)])
        self.almox.analisarRequisicao(self.pedidos, 31, aprovar=True)
        historico_antes = len(self.gestor.movimentacoes)
        with self.assertRaises(PermissionError):
            self.gestor.entregar(req, req.itens[0], 2, self.servidor)
        self.assertEqual(self.estoque.quantidadeAtual, 7)
        self.assertEqual(req.itens[0].quantidadeAtendida, 0)
        self.assertEqual(req.status, Requisicao.APROVADA)
        self.assertEqual(len(self.gestor.movimentacoes), historico_antes)

    def test_entrada_por_servidor_nao_muda_saldo(self):
        with self.assertRaises(PermissionError):
            self.gestor.registrarEntrada(self.material, 4, self.servidor)
        self.assertEqual(self.estoque.quantidadeAtual, 0)
        self.assertEqual(len(self.gestor.movimentacoes), 0)

    def test_inventario_e_ajuste_requerem_almoxarife(self):
        with self.assertRaises(PermissionError):
            self.gestor.iniciarInventario(41, self.servidor)
        self.gestor.registrarEntrada(self.material, 4, self.almox)
        inv = self.almox.realizarInventario(self.gestor, 41, [(self.material, 2)])
        with self.assertRaises(PermissionError):
            self.gestor.ajustarInventario(inv, self.servidor)
        self.assertEqual(self.estoque.quantidadeAtual, 4)
        self.assertFalse(inv.ajustado)
        ajustes = self.gestor.ajustarInventario(inv, self.almox)
        self.assertEqual(self.estoque.quantidadeAtual, 2)
        self.assertEqual([m.quantidade for m in ajustes], [2])

    def test_inventario_e_ajuste_auditavel(self):
        self.gestor.registrarEntrada(self.material, 10, self.almox)
        inv = self.almox.realizarInventario(self.gestor, 20, [(self.material, 8)])
        self.assertEqual(inv.status, "FINALIZADO")
        self.assertEqual(inv.itens[0].calcularDiferenca(), -2)
        ajustes = self.gestor.ajustarInventario(inv, self.almox)
        self.assertEqual(len(ajustes), 1)
        self.assertEqual(ajustes[0].tipo, "AJUSTE_SAIDA")
        self.assertEqual(self.estoque.quantidadeAtual, 8)
        with self.assertRaises(ValueError):
            self.gestor.ajustarInventario(inv, self.almox)

    def test_inventario_obsoleto_nao_e_ajustado(self):
        self.gestor.registrarEntrada(self.material, 10, self.almox)
        inv = self.almox.realizarInventario(self.gestor, 21, [(self.material, 8)])
        self.gestor.registrarEntrada(self.material, 1, self.almox)
        with self.assertRaisesRegex(ValueError, "O saldo mudou"):
            self.gestor.ajustarInventario(inv, self.almox)
        self.assertEqual(self.estoque.quantidadeAtual, 11)
        self.assertFalse(inv.ajustado)

    def test_rn2_historico_preservado_apos_desativacao(self):
        self.gestor.registrarEntrada(self.material, 3, self.almox)
        self.catalogo.desativarMaterial(self.material.id)
        self.assertEqual(self.estoque.quantidadeAtual, 3)
        self.assertEqual(len(self.gestor.movimentacoes), 1)
        with self.assertRaises(ValueError):
            self.servidor.criarRequisicao(self.pedidos, 4, [(self.material, 1)])


# Test Integracao
class TestIntegracao(unittest.TestCase):
    def test_menu_cadastro_e_movimentacao(self):
        menu = MenuAlmoxarifado()
        # Escolhe 2 (categoria), 3 (material), 6 (entrada), 1 (consulta) e 0 (sair).
        entradas = [
            "2", "Papelaria", "Material escolar", "",
            "3", "1", "LAP01", "Lápis", "unidade", "10", "Prateleira X", "",
            "6", "1", "100", "",
            "1", "", "0",
        ]
        saida = StringIO()
        with patch("builtins.input", side_effect=entradas), redirect_stdout(saida):
            menu.executar()
        texto = saida.getvalue()
        self.assertIn("Categoria criada: 1 - Papelaria", texto)
        self.assertIn("Material LAP01 cadastrado", texto)
        self.assertIn("Entrada registrada", texto)
        self.assertIn("saldo: 100", texto)
        self.assertIn("Sistema encerrado.", texto)


if __name__ == "__main__":
    unittest.main(verbosity=2)
