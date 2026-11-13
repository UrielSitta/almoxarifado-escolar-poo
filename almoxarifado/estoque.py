
from __future__ import annotations

from datetime import date, datetime
from itertools import count
from typing import TYPE_CHECKING

from .catalogo import Material
from .requisicoes import ItemRequisicao, Requisicao
from .usuarios import exigir_almoxarife

if TYPE_CHECKING:
    from .usuarios import Almoxarife


class Estoque:
    """Saldo físico de um material em um único almoxarifado escolar."""

    def __init__(self, id: int, material: Material, localizacao: str, quantidadeAtual: int = 0) -> None:
        if not isinstance(id, int) or id <= 0:
            raise ValueError("ID de estoque deve ser positivo.")
        if not localizacao.strip():
            raise ValueError("A localização deve ser informada.")
        if not isinstance(quantidadeAtual, int) or isinstance(quantidadeAtual, bool) or quantidadeAtual < 0:
            raise ValueError("O saldo inicial não pode ser negativo.")
        self.__id = id
        self.__material = material
        self.__localizacao = localizacao.strip()
        self.__quantidadeAtual = quantidadeAtual

    @property
    def id(self) -> int:
        return self.__id

    @property
    def material(self) -> Material:
        return self.__material

    @property
    def localizacao(self) -> str:
        return self.__localizacao

    @property
    def quantidadeAtual(self) -> int:
        return self.__quantidadeAtual

    def adicionar(self, qtd: int) -> None:
        self.__validar_quantidade(qtd)
        self.__quantidadeAtual += qtd

    def retirar(self, qtd: int) -> bool:
        self.__validar_quantidade(qtd)
        if qtd > self.__quantidadeAtual:
            return False  # RN1: saldo nunca negativo.
        self.__quantidadeAtual -= qtd
        return True

    def abaixoDoMinimo(self) -> bool:
        return self.__quantidadeAtual < self.__material.estoqueMinimo

    @staticmethod
    def __validar_quantidade(qtd: int) -> None:
        if not isinstance(qtd, int) or isinstance(qtd, bool) or qtd <= 0:
            raise ValueError("A quantidade deve ser um inteiro positivo.")


class Movimentacao:
    """Registro histórico de entrada, saída ou ajuste de estoque."""

    TIPOS = {"ENTRADA", "SAIDA", "AJUSTE_ENTRADA", "AJUSTE_SAIDA"}

    def __init__(
        self,
        id: int,
        estoque: Estoque,
        tipo: str,
        quantidade: int,
        responsavel: Almoxarife,
        itemRequisicao: ItemRequisicao | None = None,
    ) -> None:
        exigir_almoxarife(responsavel)
        self.__id = id
        self.__estoque = estoque
        self.__tipo = tipo
        self.__quantidade = quantidade
        self.__responsavel = responsavel
        self.__itemRequisicao = itemRequisicao
        self.__dataHora = datetime.now()
        if not self.validar():
            raise ValueError("Movimentação inválida.")

    @property
    def id(self) -> int:
        return self.__id

    @property
    def estoque(self) -> Estoque:
        return self.__estoque

    @property
    def tipo(self) -> str:
        return self.__tipo

    @property
    def quantidade(self) -> int:
        return self.__quantidade

    @property
    def responsavel(self) -> Almoxarife:
        return self.__responsavel

    @property
    def itemRequisicao(self) -> ItemRequisicao | None:
        return self.__itemRequisicao

    @property
    def dataHora(self) -> datetime:
        return self.__dataHora

    def validar(self) -> bool:
        return (
            isinstance(self.__id, int) and self.__id > 0
            and self.__tipo in self.TIPOS
            and isinstance(self.__quantidade, int) and not isinstance(self.__quantidade, bool)
            and self.__quantidade > 0
            and (self.__itemRequisicao is None or (
                self.__tipo == "SAIDA" and self.__itemRequisicao.material is self.__estoque.material
            ))
        )


class ItemInventario:
    """Contagem de um estoque e instantâneo do saldo de sistema."""

    def __init__(self, estoque: Estoque, quantidadeContada: int) -> None:
        if not isinstance(quantidadeContada, int) or isinstance(quantidadeContada, bool) or quantidadeContada < 0:
            raise ValueError("A contagem física não pode ser negativa.")
        self.__estoque = estoque
        self.__quantidadeSistema = estoque.quantidadeAtual
        self.__quantidadeContada = quantidadeContada

    @property
    def estoque(self) -> Estoque:
        return self.__estoque

    @property
    def quantidadeSistema(self) -> int:
        return self.__quantidadeSistema

    @property
    def quantidadeContada(self) -> int:
        return self.__quantidadeContada

    def calcularDiferenca(self) -> int:
        return self.__quantidadeContada - self.__quantidadeSistema

    def temDivergencia(self) -> bool:
        return self.calcularDiferenca() != 0


class Inventario:
    """Inventário com um ou mais itens de contagem (composição UML)."""

    ABERTO = "ABERTO"
    EM_CONTAGEM = "EM_CONTAGEM"
    FINALIZADO = "FINALIZADO"

    def __init__(self, id: int, responsavel: Almoxarife, data: date | None = None) -> None:
        exigir_almoxarife(responsavel)
        if not isinstance(id, int) or isinstance(id, bool) or id <= 0:
            raise ValueError("O ID do inventário deve ser positivo.")
        self.__id = id
        self.__responsavel = responsavel
        self.__data = data or date.today()
        self.__status = self.ABERTO
        self.__itens: list[ItemInventario] = []
        self.__ajustado = False

    @property
    def id(self) -> int:
        return self.__id

    @property
    def data(self) -> date:
        return self.__data

    @property
    def responsavel(self) -> Almoxarife:
        return self.__responsavel

    @property
    def status(self) -> str:
        return self.__status

    @property
    def itens(self) -> tuple[ItemInventario, ...]:
        return tuple(self.__itens)

    @property
    def ajustado(self) -> bool:
        return self.__ajustado

    def iniciar(self) -> None:
        if self.__status != self.ABERTO:
            raise ValueError("O inventário já foi iniciado.")
        self.__status = self.EM_CONTAGEM

    def adicionarItem(self, estoque: Estoque, quantidadeContada: int) -> ItemInventario:
        if self.__status != self.EM_CONTAGEM:
            raise ValueError("O inventário precisa estar em contagem.")
        if any(item.estoque is estoque for item in self.__itens):
            raise ValueError("Este estoque já foi contado neste inventário.")
        item = ItemInventario(estoque, quantidadeContada)
        self.__itens.append(item)
        return item

    def finalizar(self) -> bool:
        if self.__status != self.EM_CONTAGEM or not self.__itens:
            return False
        self.__status = self.FINALIZADO
        return True

    def apurarDivergencias(self) -> list[ItemInventario]:
        return [item for item in self.__itens if item.temDivergencia()]

    def marcarAjustado(self) -> None:
        if self.__status != self.FINALIZADO or self.__ajustado:
            raise ValueError("Inventário ainda não finalizado ou já ajustado.")
        self.__ajustado = True


class GestorEstoque:
    """Serviço auxiliar: garante saldo íntegro e histórico de movimentações."""

    def __init__(self) -> None:
        self.__estoques: dict[int, Estoque] = {}  # chave = ID do material
        self.__inventarios: dict[int, Inventario] = {}
        self.__movimentacoes: list[Movimentacao] = []
        self.__sequenciaEstoque = count(1)
        self.__sequenciaMovimentacao = count(1)

    @property
    def movimentacoes(self) -> tuple[Movimentacao, ...]:
        return tuple(self.__movimentacoes)

    def registrarEstoque(self, material: Material, localizacao: str) -> Estoque:
        if not material.ativo:
            raise ValueError("Não é possível abrir estoque para material desativado.")
        if material.id in self.__estoques:
            raise ValueError("O material já possui registro de estoque neste almoxarifado.")
        estoque = Estoque(next(self.__sequenciaEstoque), material, localizacao)
        self.__estoques[material.id] = estoque
        return estoque

    def consultarEstoque(self, material: Material) -> Estoque:
        try:
            estoque = self.__estoques[material.id]
        except KeyError as exc:
            raise LookupError("Material sem registro de estoque.") from exc
        if estoque.material is not material:
            raise ValueError("Material diferente do cadastrado neste registro de estoque.")
        return estoque

    def listarEstoques(self) -> list[Estoque]:
        return list(self.__estoques.values())

    def consultarItensAbaixoMinimo(self) -> list[Estoque]:
        return [e for e in self.__estoques.values() if e.material.ativo and e.abaixoDoMinimo()]

    def registrarEntrada(self, material: Material, qtd: int, responsavel: Almoxarife) -> Movimentacao:
        exigir_almoxarife(responsavel)
        if not material.ativo:
            raise ValueError("Não é possível registrar entrada para material desativado.")
        estoque = self.consultarEstoque(material)
        mov = Movimentacao(next(self.__sequenciaMovimentacao), estoque, "ENTRADA", qtd, responsavel)
        estoque.adicionar(qtd)
        self.__movimentacoes.append(mov)
        return mov

    def entregar(
        self,
        requisicao: Requisicao,
        item: ItemRequisicao,
        qtd: int,
        responsavel: Almoxarife,
    ) -> bool:
        """RN1: impede saldo negativo e registra a saída na entrega efetiva."""
        exigir_almoxarife(responsavel)
        if requisicao.almoxarife is None:
            raise ValueError("A requisição não possui um almoxarife responsável pela análise.")
        if requisicao.status not in (Requisicao.APROVADA, Requisicao.PARCIAL):
            raise ValueError("A requisição precisa estar aprovada para a entrega.")
        if item not in requisicao.itens:
            raise ValueError("Item não pertence à requisição indicada.")
        if not isinstance(qtd, int) or isinstance(qtd, bool) or qtd <= 0:
            raise ValueError("A quantidade entregue deve ser positiva.")
        if qtd > item.saldoPendente():
            raise ValueError("A entrega excede o saldo pendente do pedido.")
        estoque = self.consultarEstoque(item.material)
        if qtd > estoque.quantidadeAtual:
            return False
        # Criar e validar movimento antes de realizar qualquer mutação.
        mov = Movimentacao(next(self.__sequenciaMovimentacao), estoque, "SAIDA", qtd, responsavel, item)
        if not estoque.retirar(qtd):
            return False
        if not item.atender(qtd):
            estoque.adicionar(qtd)  # Reverte a saída se o item não aceitar o atendimento.
            raise RuntimeError("Não foi possível registrar a entrega na requisição.")
        requisicao.registrarAtendimento()
        self.__movimentacoes.append(mov)
        return True

    def iniciarInventario(self, id: int, responsavel: Almoxarife) -> Inventario:
        exigir_almoxarife(responsavel)
        if id in self.__inventarios:
            raise ValueError("ID de inventário já utilizado.")
        inventario = Inventario(id, responsavel)
        inventario.iniciar()
        self.__inventarios[id] = inventario
        return inventario

    def consultarInventario(self, id: int) -> Inventario:
        try:
            return self.__inventarios[id]
        except KeyError as exc:
            raise LookupError("Inventário não encontrado.") from exc

    def ajustarInventario(self, inventario: Inventario, responsavel: Almoxarife) -> list[Movimentacao]:
        """Aplica divergências e gera movimentações de ajuste auditáveis.

        Exige almoxarife e impede ajustes obsoletos ou repetidos.
        """
        exigir_almoxarife(responsavel)
        if self.__inventarios.get(inventario.id) is not inventario:
            raise ValueError("Inventário não cadastrado neste gestor.")
        if inventario.status != Inventario.FINALIZADO or inventario.ajustado:
            raise ValueError("O inventário deve estar finalizado e ainda não ajustado.")
        for item in inventario.itens:
            if self.consultarEstoque(item.estoque.material) is not item.estoque:
                raise ValueError("Item do inventário refere-se a outro almoxarifado.")
            if item.estoque.quantidadeAtual != item.quantidadeSistema:
                raise ValueError("O saldo mudou após a contagem. É necessário novo inventário.")
        movimentos: list[Movimentacao] = []
        for item in inventario.apurarDivergencias():
            delta = item.calcularDiferenca()
            tipo = "AJUSTE_ENTRADA" if delta > 0 else "AJUSTE_SAIDA"
            movimento = Movimentacao(
                next(self.__sequenciaMovimentacao), item.estoque, tipo, abs(delta), responsavel
            )
            movimentos.append(movimento)
        for movimento in movimentos:
            if movimento.tipo == "AJUSTE_ENTRADA":
                movimento.estoque.adicionar(movimento.quantidade)
            else:
                if not movimento.estoque.retirar(movimento.quantidade):
                    raise RuntimeError("Falha de consistência ao aplicar ajuste de saída.")
            self.__movimentacoes.append(movimento)
        inventario.marcarAjustado()
        return movimentos

    def emitirRelatorio(self) -> str:
        linhas = ["RELATÓRIO DE ESTOQUE DO ALMOXARIFADO ESCOLAR"]
        for estoque in sorted(self.__estoques.values(), key=lambda e: e.material.codigo):
            linhas.append(
                f"{estoque.material.codigo} | {estoque.material.nome} | "
                f"saldo: {estoque.quantidadeAtual} {estoque.material.unidade} | "
                f"mínimo: {estoque.material.estoqueMinimo} | "
                f"situação: {'INATIVO' if not estoque.material.ativo else ('ABAIXO DO MÍNIMO' if estoque.abaixoDoMinimo() else 'OK')}"
            )
        linhas.append(f"Movimentações registradas: {len(self.__movimentacoes)}")
        return "\n".join(linhas)
