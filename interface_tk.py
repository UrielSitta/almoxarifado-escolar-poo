import tkinter as tk
from tkinter import ttk, messagebox

from almoxarifado.catalogo import Categoria, Material, Catalogo
from almoxarifado.estoque import GestorEstoque
from almoxarifado.requisicoes import GerenciadorRequisicoes
from almoxarifado.usuarios import Almoxarife, Servidor


class Sistema(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Almoxarifado Escolar")
        self.geometry("900x640")

        # Objetos da Parte 2: o Tkinter apenas chama seus métodos.
        self.catalogo = Catalogo()
        self.estoque = GestorEstoque()
        self.pedidos = GerenciadorRequisicoes(self.catalogo)
        self.almoxarife = Almoxarife(1, "Almoxarife", "almox@escola.edu.br", "senha123", "001")
        self.servidor = Servidor(2, "Servidor", "servidor@escola.edu.br", "senha123", "Escola")
        self.id_categoria = 1
        self.id_material = 1
        self.id_pedido = 1

        ttk.Label(self, text="Sistema de Almoxarifado Escolar",
                  font=("Arial", 17, "bold")).pack(pady=16)
        abas = ttk.Notebook(self)
        abas.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        self.aba_materiais = ttk.Frame(abas, padding=12)
        self.aba_estoque = ttk.Frame(abas, padding=12)
        self.aba_pedidos = ttk.Frame(abas, padding=12)
        abas.add(self.aba_materiais, text="Materiais")
        abas.add(self.aba_estoque, text="Estoque")
        abas.add(self.aba_pedidos, text="Requisições")

        self.montar_materiais()
        self.montar_estoque()
        self.montar_pedidos()
        self.atualizar_listas()

    def campo(self, pai, texto, linha, coluna, largura=18):
        ttk.Label(pai, text=texto).grid(row=linha, column=coluna, sticky="w", padx=5, pady=5)
        entrada = ttk.Entry(pai, width=largura)
        entrada.grid(row=linha, column=coluna + 1, padx=5, pady=5)
        return entrada

    def tabela(self, pai, colunas, alturas=10):
        tabela = ttk.Treeview(pai, columns=colunas, show="headings", height=alturas)
        for nome in colunas:
            tabela.heading(nome, text=nome)
            tabela.column(nome, width=105, anchor="center")
        tabela.pack(fill="both", expand=True, pady=10)
        return tabela

    def executar(self, funcao):
        try:
            resultado = funcao()
            self.atualizar_listas()
            if resultado:
                messagebox.showinfo("Sucesso", resultado)
        except (ValueError, TypeError, LookupError, PermissionError, RuntimeError) as erro:
            messagebox.showerror("Erro", str(erro))

    def montar_materiais(self):
        area = self.aba_materiais
        categoria = ttk.LabelFrame(area, text="Cadastrar categoria", padding=8)
        categoria.pack(fill="x", pady=5)
        self.nome_categoria = self.campo(categoria, "Nome:", 0, 0, 30)
        ttk.Button(categoria, text="Cadastrar", command=lambda:
                   self.executar(self.cadastrar_categoria)).grid(row=0, column=2, padx=8)

        material = ttk.LabelFrame(area, text="Cadastrar material", padding=8)
        material.pack(fill="x", pady=5)
        self.nome_material = self.campo(material, "Material:", 0, 0)
        self.codigo_material = self.campo(material, "Código:", 0, 2)
        self.unidade_material = self.campo(material, "Unidade:", 1, 0)
        self.minimo_material = self.campo(material, "Mínimo:", 1, 2)
        ttk.Label(material, text="Categoria:").grid(row=2, column=0, sticky="w", padx=5)
        self.escolha_categoria = ttk.Combobox(material, state="readonly", width=20)
        self.escolha_categoria.grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(material, text="Cadastrar material", command=lambda:
                   self.executar(self.cadastrar_material)).grid(row=2, column=2, columnspan=2)

        self.tabela_materiais = self.tabela(area, ("ID", "Código", "Material", "Categoria", "Situação"), 9)
        ttk.Button(area, text="Desativar material selecionado", command=lambda:
                   self.executar(self.desativar_material)).pack(anchor="w")

    def montar_estoque(self):
        area = self.aba_estoque
        formulario = ttk.LabelFrame(area, text="Registrar entrada de material", padding=12)
        formulario.pack(fill="x", pady=8)
        ttk.Label(formulario, text="Material:").grid(row=0, column=0, padx=5)
        self.escolha_entrada = ttk.Combobox(formulario, width=30, state="readonly")
        self.escolha_entrada.grid(row=0, column=1, padx=5)
        self.quantidade_entrada = self.campo(formulario, "Quantidade:", 0, 2, 12)
        ttk.Button(formulario, text="Registrar entrada", command=lambda:
                   self.executar(self.registrar_entrada)).grid(row=0, column=4, padx=8)
        ttk.Label(area, text="Saldos atuais", font=("Arial", 11, "bold")).pack(anchor="w", pady=(10, 0))
        self.tabela_estoque = self.tabela(area, ("ID", "Material", "Saldo", "Mínimo", "Situação"), 15)

    def montar_pedidos(self):
        area = self.aba_pedidos
        formulario = ttk.LabelFrame(area, text="Nova requisição", padding=12)
        formulario.pack(fill="x", pady=8)
        ttk.Label(formulario, text="Material:").grid(row=0, column=0, padx=5)
        self.escolha_pedido = ttk.Combobox(formulario, width=28, state="readonly")
        self.escolha_pedido.grid(row=0, column=1, padx=5)
        self.quantidade_pedido = self.campo(formulario, "Quantidade:", 0, 2, 12)
        ttk.Button(formulario, text="Solicitar", command=lambda:
                   self.executar(self.criar_pedido)).grid(row=0, column=4, padx=8)

        ttk.Label(area, text="Selecione um pedido na tabela para aprovar, recusar ou entregar.").pack(anchor="w", pady=(8, 0))
        self.tabela_pedidos = self.tabela(area, ("Pedido", "Material", "Solicitado", "Entregue", "Status"), 12)
        botoes = ttk.Frame(area)
        botoes.pack(fill="x", pady=5)
        ttk.Button(botoes, text="Aprovar", command=lambda:
                   self.executar(lambda: self.analisar_pedido(True))).pack(side="left", padx=5)
        ttk.Button(botoes, text="Recusar", command=lambda:
                   self.executar(lambda: self.analisar_pedido(False))).pack(side="left", padx=5)
        ttk.Label(botoes, text="Quantidade a entregar:").pack(side="left", padx=(30, 5))
        self.quantidade_entrega = ttk.Entry(botoes, width=10)
        self.quantidade_entrega.pack(side="left")
        ttk.Button(botoes, text="Entregar", command=lambda:
                   self.executar(self.entregar_pedido)).pack(side="left", padx=10)

    def selecionar_id(self, caixa):
        valor = caixa.get()
        if not valor:
            raise ValueError("Selecione um item da lista.")
        return int(valor.split(" - ", 1)[0])

    def pedido_selecionado(self):
        selecionados = self.tabela_pedidos.selection()
        if not selecionados:
            raise ValueError("Selecione uma requisição na tabela.")
        id_pedido = int(self.tabela_pedidos.item(selecionados[0], "values")[0])
        return self.pedidos.consultarRequisicao(id_pedido)

    def cadastrar_categoria(self):
        categoria = Categoria(self.id_categoria, self.nome_categoria.get())
        self.catalogo.cadastrarCategoria(categoria)
        self.id_categoria += 1
        self.nome_categoria.delete(0, "end")
        return "Categoria cadastrada."

    def cadastrar_material(self):
        categoria = self.catalogo.consultarCategoria(self.selecionar_id(self.escolha_categoria))
        material = Material(self.id_material, self.codigo_material.get(),
                            self.nome_material.get(), self.unidade_material.get(),
                            int(self.minimo_material.get()), categoria)
        self.almoxarife.cadastrarMaterial(self.catalogo, material)
        self.estoque.registrarEstoque(material, "Almoxarifado")
        self.id_material += 1
        for entrada in (self.nome_material, self.codigo_material, self.unidade_material, self.minimo_material):
            entrada.delete(0, "end")
        return "Material cadastrado."

    def desativar_material(self):
        selecionados = self.tabela_materiais.selection()
        if not selecionados:
            raise ValueError("Selecione um material na tabela.")
        id_material = int(self.tabela_materiais.item(selecionados[0], "values")[0])
        self.catalogo.desativarMaterial(id_material)
        return "Material desativado."

    def registrar_entrada(self):
        material = self.catalogo.consultarMaterial(self.selecionar_id(self.escolha_entrada))
        self.almoxarife.registrarMovimentacao(self.estoque, material, int(self.quantidade_entrada.get()))
        self.quantidade_entrada.delete(0, "end")
        return "Entrada registrada."

    def criar_pedido(self):
        material = self.catalogo.consultarMaterial(self.selecionar_id(self.escolha_pedido))
        self.servidor.criarRequisicao(self.pedidos, self.id_pedido,
                                     [(material, int(self.quantidade_pedido.get()))])
        self.id_pedido += 1
        self.quantidade_pedido.delete(0, "end")
        return "Requisição criada."

    def analisar_pedido(self, aprovar):
        pedido = self.pedido_selecionado()
        if not self.almoxarife.analisarRequisicao(self.pedidos, pedido.id, aprovar):
            raise ValueError("Esse pedido não pode mais ser analisado.")
        return "Requisição aprovada." if aprovar else "Requisição recusada."

    def entregar_pedido(self):
        pedido = self.pedido_selecionado()
        quantidade = int(self.quantidade_entrega.get())
        if not self.estoque.entregar(pedido, pedido.itens[0], quantidade, self.almoxarife):
            raise ValueError("Estoque insuficiente para essa entrega.")
        self.quantidade_entrega.delete(0, "end")
        return "Material entregue."

    def atualizar_listas(self):
        categorias = [f"{c.id} - {c.nome}" for c in self.catalogo.listarCategorias()]
        materiais = self.catalogo.listarMateriais(incluirInativos=True)
        ativos = [m for m in materiais if m.ativo]
        opcoes = [f"{m.id} - {m.nome}" for m in ativos]
        self.escolha_categoria["values"] = categorias
        self.escolha_entrada["values"] = opcoes
        self.escolha_pedido["values"] = opcoes
        for caixa in (self.escolha_categoria, self.escolha_entrada, self.escolha_pedido):
            if caixa.get() not in caixa["values"]:
                caixa.set(caixa["values"][0] if caixa["values"] else "")

        for tabela in (self.tabela_materiais, self.tabela_estoque, self.tabela_pedidos):
            tabela.delete(*tabela.get_children())
        for material in materiais:
            saldo = self.estoque.consultarEstoque(material).quantidadeAtual
            self.tabela_materiais.insert("", "end", values=(
                material.id, material.codigo, material.nome, material.categoria.nome,
                "Ativo" if material.ativo else "Inativo"))
            self.tabela_estoque.insert("", "end", values=(
                material.id, material.nome, saldo, material.estoqueMinimo,
                "Inativo" if not material.ativo else
                ("Abaixo do mínimo" if saldo < material.estoqueMinimo else "OK")))
        for pedido in self.pedidos.listarRequisicoes():
            item = pedido.itens[0]
            self.tabela_pedidos.insert("", "end", values=(
                pedido.id, item.material.nome, item.quantidadeSolicitada,
                item.quantidadeAtendida, pedido.status))


if __name__ == "__main__":
    Sistema().mainloop()
