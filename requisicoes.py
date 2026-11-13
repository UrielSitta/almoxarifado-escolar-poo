from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from .catalogo import Catalogo, Material
from .usuarios import exigir_almoxarife, exigir_servidor

if TYPE_CHECKING:
    from .usuarios import Almoxarife, Servidor


class ItemRequisicao:
    """Item vinculado a uma Requisicao (composição no diagrama UML)."""

    def __init__(self, material: Material, quantidadeSolicitada: int) -> None:
        if not isinstance(material, Material):
            raise TypeError("O item deve referenciar um material válido.")
        if not isinstance(quantidadeSolicitada, int) or isinstance(quantidadeSolicitada, bool) or quantidadeSolicitada <= 0:
            raise ValueError("A quantidade solicitada deve ser inteira e positiva.")
        self.__material = material
        self.__quantidadeSolicitada = quantidadeSolicitada
        self.__quantidadeAtendida = 0

    @property
    def material(self) -> Material:
        return self.__material

    @property
    def quantidadeSolicitada(self) -> int:
        return self.__quantidadeSolicitada

    @property
    def quantidadeAtendida(self) -> int:
        return self.__quantidadeAtendida

    def saldoPendente(self) -> int:
        return self.__quantidadeSolicitada - self.__quantidadeAtendida

    def atender(self, qtd: int) -> bool:
        """Registra atendimento após validação externa do estoque disponível."""
        if not isinstance(qtd, int) or isinstance(qtd, bool) or qtd <= 0:
            raise ValueError("A quantidade atendida deve ser inteira e positiva.")
        if qtd > self.saldoPendente():
            return False
        self.__quantidadeAtendida += qtd
        return True


class Requisicao:
    """Pedido de um servidor, com uma ou mais linhas e status auditável."""

    PENDENTE = "PENDENTE"
    APROVADA = "APROVADA"
    RECUSADA = "RECUSADA"
    PARCIAL = "PARCIAL"
    ATENDIDA = "ATENDIDA"

    def __init__(self, id: int, solicitante: Servidor, data: date | None = None) -> None:
        if not isinstance(id, int) or isinstance(id, bool) or id <= 0:
            raise ValueError("O ID da requisição deve ser positivo.")
        exigir_servidor(solicitante)
        self.__id = id
        self.__data = data or date.today()
        self.__solicitante = solicitante
        self.__status = self.PENDENTE
        self.__almoxarife: Almoxarife | None = None
        self.__itens: list[ItemRequisicao] = []

    @property
    def id(self) -> int:
        return self.__id

    @property
    def data(self) -> date:
        return self.__data

    @property
    def solicitante(self) -> Servidor:
        return self.__solicitante

    @property
    def status(self) -> str:
        return self.__status

    @property
    def almoxarife(self) -> Almoxarife | None:
        return self.__almoxarife

    @property
    def itens(self) -> tuple[ItemRequisicao, ...]:
        return tuple(self.__itens)

    def adicionarItem(self, material: Material, quantidade: int) -> ItemRequisicao:
        if self.__status != self.PENDENTE:
            raise ValueError("Somente requisições pendentes podem receber itens.")
        if not material.ativo:
            raise ValueError("RN2: não é permitido solicitar materiais desativados.")
        if any(item.material is material for item in self.__itens):
            raise ValueError("Material duplicado na mesma requisição.")
        item = ItemRequisicao(material, quantidade)
        self.__itens.append(item)
        return item

    def pendente(self) -> bool:
        return self.__status == self.PENDENTE

    def aprovar(self, responsavel: Almoxarife) -> bool:
        exigir_almoxarife(responsavel)
        if not self.pendente() or not self.__itens:
            return False
        self.__almoxarife = responsavel
        self.__status = self.APROVADA
        return True

    def recusar(self, responsavel: Almoxarife) -> bool:
        exigir_almoxarife(responsavel)
        if not self.pendente():
            return False
        self.__almoxarife = responsavel
        self.__status = self.RECUSADA
        return True

    def registrarAtendimento(self) -> None:
        """Recalcula o status a partir das quantidades efetivamente entregues."""
        if self.__status not in (self.APROVADA, self.PARCIAL):
            raise ValueError("A requisição deve estar aprovada para receber materiais.")
        if all(item.saldoPendente() == 0 for item in self.__itens):
            self.__status = self.ATENDIDA
        elif any(item.quantidadeAtendida > 0 for item in self.__itens):
            self.__status = self.PARCIAL


class GerenciadorRequisicoes:
    """Serviço auxiliar que aplica as regras de criação e decisão de pedidos."""

    def __init__(self, catalogo: Catalogo) -> None:
        self.__catalogo = catalogo
        self.__requisicoes: dict[int, Requisicao] = {}

    def criarRequisicao(
        self,
        id: int,
        solicitante: Servidor,
        itens: list[tuple[Material, int]],
    ) -> Requisicao:
        exigir_servidor(solicitante)
        if id in self.__requisicoes:
            raise ValueError("ID de requisição já utilizado.")
        if not itens:
            raise ValueError("A requisição precisa conter pelo menos um material.")
        # Validação completa antes do cadastro: nenhuma solicitação parcialmente criada.
        req = Requisicao(id, solicitante)
        for material, quantidade in itens:
            if self.__catalogo.consultarMaterial(material.id) is not material:
                raise ValueError("Material não pertence a este catálogo.")
            req.adicionarItem(material, quantidade)
        self.__requisicoes[id] = req
        return req

    def consultarRequisicao(self, id: int) -> Requisicao:
        try:
            return self.__requisicoes[id]
        except KeyError as exc:
            raise LookupError("Requisição não encontrada.") from exc

    def listarRequisicoes(self, status: str | None = None) -> list[Requisicao]:
        return [r for r in self.__requisicoes.values() if status is None or r.status == status]

    def analisarRequisicao(self, id: int, responsavel: Almoxarife, aprovar: bool) -> bool:
        exigir_almoxarife(responsavel)
        if not isinstance(aprovar, bool):
            raise ValueError("A decisão deve ser True (aprovar) ou False (recusar).")
        req = self.consultarRequisicao(id)
        return req.aprovar(responsavel) if aprovar else req.recusar(responsavel)
