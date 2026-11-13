

from __future__ import annotations

from abc import ABC, abstractmethod
import hashlib
import hmac
import secrets
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .catalogo import Catalogo, Material
    from .estoque import GestorEstoque, Inventario, Movimentacao
    from .requisicoes import GerenciadorRequisicoes, Requisicao


class Usuario(ABC):
    """Base abstrata de todos os atores autenticados no sistema."""

    def __init__(self, id: int, nome: str, email: str, senha: str) -> None:
        if not isinstance(id, int) or id <= 0:
            raise ValueError("O ID do usuário deve ser positivo.")
        if not nome.strip():
            raise ValueError("O nome do usuário é obrigatório.")
        if "@" not in email or not email.strip():
            raise ValueError("Informe um e-mail válido.")
        if len(senha) < 6:
            raise ValueError("A senha deve ter pelo menos 6 caracteres.")
        self.__id = id
        self.__nome = nome.strip()
        self.__email = email.strip().lower()
        self.__salt = secrets.token_bytes(16)
        self.__senhaHash = self.__criar_hash(senha)

    def __criar_hash(self, senha: str) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), self.__salt, 120_000)

    @property
    def id(self) -> int:
        return self.__id

    @property
    def nome(self) -> str:
        return self.__nome

    @property
    def email(self) -> str:
        return self.__email

    def autenticar(self, senha: str) -> bool:
        """Confere a senha sem expor sua representação armazenada."""
        return hmac.compare_digest(self.__senhaHash, self.__criar_hash(senha))

    def atualizarDados(self, *, nome: str | None = None, email: str | None = None) -> None:
        if nome is not None and not nome.strip():
            raise ValueError("O nome do usuário é obrigatório.")
        if email is not None and "@" not in email:
            raise ValueError("O e-mail precisa conter @.")
        if nome is not None:
            self.__nome = nome.strip()
        if email is not None:
            self.__email = email.strip().lower()

    @abstractmethod
    def permissoes(self) -> list[str]:
        """Cada subclasse informa seu próprio conjunto de permissões."""

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self.id}, nome={self.nome!r})"


class Administrador(Usuario):
    """Responsável por contas de usuários e relatórios gerais."""

    def __init__(self, id: int, nome: str, email: str, senha: str, nivelAcesso: int = 1) -> None:
        super().__init__(id, nome, email, senha)
        if nivelAcesso < 1:
            raise ValueError("O nível de acesso deve ser positivo.")
        self.__nivelAcesso = nivelAcesso

    @property
    def nivelAcesso(self) -> int:
        return self.__nivelAcesso

    def permissoes(self) -> list[str]:
        return ["Gerenciar usuários", "Emitir relatórios de estoque"]

    def gerenciarUsuarios(self, cadastro: CadastroUsuarios, acao: str, **dados: object) -> object:
        """Encaminha operações de cadastro, consulta, atualização e exclusão."""
        if acao == "cadastrar":
            return cadastro.cadastrar(dados["usuario"])
        if acao == "consultar":
            return cadastro.consultar(dados["id"])
        if acao == "listar":
            return cadastro.listar()
        if acao == "atualizar":
            return cadastro.atualizar(dados["id"], nome=dados.get("nome"), email=dados.get("email"))
        if acao == "excluir":
            return cadastro.excluir(dados["id"])
        raise ValueError("Operação de gerenciamento de usuários desconhecida.")

    def emitirRelatorio(self, gestor: GestorEstoque) -> str:
        return gestor.emitirRelatorio()


class Almoxarife(Usuario):
    """Responsável por material, estoque, solicitações e inventários."""

    def __init__(self, id: int, nome: str, email: str, senha: str, matricula: str) -> None:
        super().__init__(id, nome, email, senha)
        if not matricula.strip():
            raise ValueError("A matrícula deve ser informada.")
        self.__matricula = matricula.strip()

    @property
    def matricula(self) -> str:
        return self.__matricula

    def permissoes(self) -> list[str]:
        return [
            "Consultar estoque", "Cadastrar material", "Atualizar material", "Desativar material",
            "Gerenciar categorias", "Registrar entrada de estoque", "Analisar solicitações",
            "Entregar materiais", "Registrar saída de estoque", "Realizar inventário físico",
            "Consultar itens abaixo do mínimo",
        ]

    def cadastrarMaterial(self, catalogo: Catalogo, material: Material) -> Material:
        catalogo.cadastrarMaterial(material)
        return material

    def analisarRequisicao(
        self, gerenciador: GerenciadorRequisicoes, id: int, aprovar: bool
    ) -> bool:
        return gerenciador.analisarRequisicao(id, self, aprovar)

    def registrarMovimentacao(
        self, gestor: GestorEstoque, material: Material, qtd: int
    ) -> Movimentacao:
        """Registra a entrada; saídas devem ocorrer pela entrega de requisições."""
        return gestor.registrarEntrada(material, qtd, self)

    def realizarInventario(
        self, gestor: GestorEstoque, id: int, contagens: list[tuple[Material, int]]
    ) -> Inventario:
        """Conta materiais e finaliza o documento, sem ajustar saldos automaticamente."""
        if not contagens:
            raise ValueError("O inventário precisa de pelo menos uma contagem.")
        # Faz as validações antes de criar o registro.
        ids: set[int] = set()
        for material, qtd in contagens:
            if material.id in ids:
                raise ValueError("Material repetido na contagem.")
            ids.add(material.id)
            gestor.consultarEstoque(material)
            if not isinstance(qtd, int) or isinstance(qtd, bool) or qtd < 0:
                raise ValueError("A contagem precisa ser inteira e não negativa.")
        inventario = gestor.iniciarInventario(id, self)
        for material, qtd in contagens:
            inventario.adicionarItem(gestor.consultarEstoque(material), qtd)
        inventario.finalizar()
        return inventario


class Servidor(Usuario):
    """Solicita materiais e acompanha apenas seus próprios pedidos."""

    def __init__(self, id: int, nome: str, email: str, senha: str, setor: str) -> None:
        super().__init__(id, nome, email, senha)
        if not setor.strip():
            raise ValueError("O setor deve ser informado.")
        self.__setor = setor.strip()

    @property
    def setor(self) -> str:
        return self.__setor

    def permissoes(self) -> list[str]:
        return ["Consultar catálogo", "Solicitar materiais", "Acompanhar solicitação"]

    def criarRequisicao(
        self, gerenciador: GerenciadorRequisicoes, id: int, itens: list[tuple[Material, int]]
    ) -> Requisicao:
        return gerenciador.criarRequisicao(id, self, itens)

    def acompanharRequisicao(self, gerenciador: GerenciadorRequisicoes, id: int) -> str:
        requisicao = gerenciador.consultarRequisicao(id)
        if requisicao.solicitante is not self:
            raise PermissionError("O servidor não pode acompanhar pedidos de outras pessoas.")
        return requisicao.status


def exigir_almoxarife(usuario: object) -> Almoxarife:
    """Bloqueia ações administrativas de estoque por perfis não autorizados."""
    if not isinstance(usuario, Almoxarife):
        raise PermissionError("Somente um almoxarife pode executar esta operação.")
    return usuario


def exigir_servidor(usuario: object) -> Servidor:
    """Garante que apenas um servidor solicitante abra requisições."""
    if not isinstance(usuario, Servidor):
        raise PermissionError("Somente um servidor pode solicitar materiais.")
    return usuario


class CadastroUsuarios:
    """Serviço auxiliar para o CRUD dos usuários, preservando referências históricas."""

    def __init__(self) -> None:
        self.__usuarios: dict[int, Usuario] = {}

    def cadastrar(self, usuario: Usuario) -> Usuario:
        if usuario.id in self.__usuarios:
            raise ValueError("ID de usuário já utilizado.")
        if any(u.email == usuario.email for u in self.__usuarios.values()):
            raise ValueError("E-mail já cadastrado.")
        self.__usuarios[usuario.id] = usuario
        return usuario

    def consultar(self, id: int) -> Usuario:
        try:
            return self.__usuarios[id]
        except KeyError as exc:
            raise LookupError("Usuário não encontrado.") from exc

    def listar(self) -> list[Usuario]:
        return list(self.__usuarios.values())

    def atualizar(self, id: int, *, nome: str | None = None, email: str | None = None) -> None:
        usuario = self.consultar(id)
        if email is not None and any(
            u.id != id and u.email == email.strip().lower() for u in self.__usuarios.values()
        ):
            raise ValueError("E-mail já pertence a outro usuário.")
        usuario.atualizarDados(nome=nome, email=email)

    def excluir(self, id: int) -> Usuario:
        try:
            return self.__usuarios.pop(id)
        except KeyError as exc:
            raise LookupError("Usuário não encontrado.") from exc
