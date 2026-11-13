
from __future__ import annotations


class Categoria:
    """Agrupa materiais semelhantes e permite sua classificação."""

    def __init__(self, id: int, nome: str, descricao: str = "") -> None:
        if id <= 0:
            raise ValueError("O ID da categoria deve ser positivo.")
        if not nome.strip():
            raise ValueError("O nome da categoria é obrigatório.")
        self.__id = id
        self.__nome = nome.strip()
        self.__descricao = descricao.strip()
        self.__ativa = True

    @property
    def id(self) -> int:
        return self.__id

    @property
    def nome(self) -> str:
        return self.__nome

    @property
    def descricao(self) -> str:
        return self.__descricao

    @property
    def ativa(self) -> bool:
        return self.__ativa

    def atualizarDescricao(self, texto: str) -> None:
        self.__descricao = texto.strip()

    def atualizarNome(self, nome: str) -> None:
        if not nome.strip():
            raise ValueError("O nome da categoria é obrigatório.")
        self.__nome = nome.strip()

    def desativar(self) -> None:
        self.__ativa = False

    def __repr__(self) -> str:
        return f"Categoria(id={self.id}, nome={self.nome!r}, ativa={self.ativa})"


class Material:
    """Material cadastrado, classificado por uma categoria.

    Exclusão é lógica: o objeto e o histórico permanecem disponíveis.
    """

    def __init__(
        self,
        id: int,
        codigo: str,
        nome: str,
        unidade: str,
        estoqueMinimo: int,
        categoria: Categoria,
    ) -> None:
        if id <= 0:
            raise ValueError("O ID do material deve ser positivo.")
        if not codigo.strip() or not nome.strip() or not unidade.strip():
            raise ValueError("Código, nome e unidade são obrigatórios.")
        if not isinstance(estoqueMinimo, int) or isinstance(estoqueMinimo, bool) or estoqueMinimo < 0:
            raise ValueError("O estoque mínimo deve ser inteiro e não negativo.")
        if not isinstance(categoria, Categoria) or not categoria.ativa:
            raise ValueError("O material precisa de uma categoria ativa.")
        self.__id = id
        self.__codigo = codigo.strip().upper()
        self.__nome = nome.strip()
        self.__unidade = unidade.strip()
        self.__estoqueMinimo = estoqueMinimo
        self.__categoria = categoria
        self.__ativo = True

    @property
    def id(self) -> int:
        return self.__id

    @property
    def codigo(self) -> str:
        return self.__codigo

    @property
    def nome(self) -> str:
        return self.__nome

    @property
    def unidade(self) -> str:
        return self.__unidade

    @property
    def estoqueMinimo(self) -> int:
        return self.__estoqueMinimo

    @property
    def categoria(self) -> Categoria:
        return self.__categoria

    @property
    def ativo(self) -> bool:
        return self.__ativo

    def atualizarDados(
        self,
        *,
        nome: str | None = None,
        unidade: str | None = None,
        estoqueMinimo: int | None = None,
        categoria: Categoria | None = None,
    ) -> None:
        """Altera campos permitidos sem reescrever a identidade do material."""
        if not self.ativo:
            raise ValueError("Não é possível editar um material desativado.")
        # Validar tudo antes de aplicar para evitar atualização parcial.
        if nome is not None and not nome.strip():
            raise ValueError("O nome do material é obrigatório.")
        if unidade is not None and not unidade.strip():
            raise ValueError("A unidade é obrigatória.")
        if estoqueMinimo is not None and (not isinstance(estoqueMinimo, int) or isinstance(estoqueMinimo, bool) or estoqueMinimo < 0):
            raise ValueError("O estoque mínimo deve ser inteiro e não negativo.")
        if categoria is not None and (not isinstance(categoria, Categoria) or not categoria.ativa):
            raise ValueError("A categoria precisa estar ativa.")
        if nome is not None:
            self.__nome = nome.strip()
        if unidade is not None:
            self.__unidade = unidade.strip()
        if estoqueMinimo is not None:
            self.__estoqueMinimo = estoqueMinimo
        if categoria is not None:
            self.__categoria = categoria

    def desativar(self) -> bool:
        """Marca como inativo, mas não apaga requisições e movimentações antigas."""
        if not self.__ativo:
            return False
        self.__ativo = False
        return True

    def __repr__(self) -> str:
        return f"Material(id={self.id}, codigo={self.codigo!r}, ativo={self.ativo})"


class Catalogo:
    """Serviço auxiliar: gerencia o CRUD de Categoria e Material em memória."""

    def __init__(self) -> None:
        self.__categorias: dict[int, Categoria] = {}
        self.__materiais: dict[int, Material] = {}
        self.__codigos: dict[str, int] = {}

    def cadastrarCategoria(self, categoria: Categoria) -> None:
        if categoria.id in self.__categorias:
            raise ValueError("ID de categoria já cadastrado.")
        if not categoria.ativa:
            raise ValueError("Não é possível cadastrar uma categoria inativa.")
        self.__categorias[categoria.id] = categoria

    def consultarCategoria(self, id: int) -> Categoria:
        try:
            return self.__categorias[id]
        except KeyError as exc:
            raise LookupError("Categoria não encontrada.") from exc

    def listarCategorias(self, incluirInativas: bool = False) -> list[Categoria]:
        return [c for c in self.__categorias.values() if incluirInativas or c.ativa]

    def atualizarCategoria(self, id: int, *, nome: str | None = None, descricao: str | None = None) -> None:
        categoria = self.consultarCategoria(id)
        if not categoria.ativa:
            raise ValueError("Categoria inativa não pode ser editada.")
        if nome is not None and not nome.strip():
            raise ValueError("O nome da categoria é obrigatório.")
        if nome is not None:
            categoria.atualizarNome(nome)
        if descricao is not None:
            categoria.atualizarDescricao(descricao)

    def desativarCategoria(self, id: int) -> None:
        categoria = self.consultarCategoria(id)
        if any(m.ativo and m.categoria is categoria for m in self.__materiais.values()):
            raise ValueError("Desative ou reclassifique os materiais antes de desativar a categoria.")
        categoria.desativar()

    def cadastrarMaterial(self, material: Material) -> None:
        if material.id in self.__materiais:
            raise ValueError("ID de material já cadastrado.")
        if material.codigo in self.__codigos:
            raise ValueError("Código de material já utilizado (inclusive por material inativo).")
        if self.__categorias.get(material.categoria.id) is not material.categoria:
            raise ValueError("A categoria do material não está cadastrada neste catálogo.")
        if not material.ativo:
            raise ValueError("Não é possível cadastrar material inativo.")
        self.__materiais[material.id] = material
        self.__codigos[material.codigo] = material.id

    def consultarMaterial(self, id: int) -> Material:
        try:
            return self.__materiais[id]
        except KeyError as exc:
            raise LookupError("Material não encontrado.") from exc

    def buscarPorCodigo(self, codigo: str) -> Material:
        try:
            return self.__materiais[self.__codigos[codigo.strip().upper()]]
        except KeyError as exc:
            raise LookupError("Código de material não encontrado.") from exc

    def listarMateriais(self, incluirInativos: bool = False) -> list[Material]:
        return [m for m in self.__materiais.values() if incluirInativos or m.ativo]

    def atualizarMaterial(self, id: int, **alteracoes: object) -> None:
        material = self.consultarMaterial(id)
        # A identidade codigo/id é imutável para manter a integridade do histórico.
        campos_permitidos = {"nome", "unidade", "estoqueMinimo", "categoria"}
        if not set(alteracoes).issubset(campos_permitidos):
            raise ValueError("Atributo de material não permitido para atualização.")
        if "categoria" in alteracoes:
            categoria = alteracoes["categoria"]
            if not isinstance(categoria, Categoria) or self.__categorias.get(categoria.id) is not categoria:
                raise ValueError("Categoria não cadastrada no catálogo.")
        material.atualizarDados(**alteracoes)

    def desativarMaterial(self, id: int) -> bool:
        return self.consultarMaterial(id).desativar()
