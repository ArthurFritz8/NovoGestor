import sqlite3
import os
from datetime import datetime
from MeuEstoque.logger import get_logger

class DatabaseManager:
    def __init__(self, db_name="estoque.db"):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.logger = get_logger(self.__class__.__name__)
        self._connect()
        self._create_tables()
        self._add_initial_brands()

    def _connect(self):
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
            self.logger.info("Conexão com o banco de dados estabelecida.")
        except sqlite3.Error as e:
            self.logger.critical(f"Erro ao conectar ao banco de dados: {e}", exc_info=True)
            print(f"Erro ao conectar ao banco de dados: {e}")

    def _create_tables(self):
        if not self.conn:
            return

        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS marcas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE
                )
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS produtos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome_produto TEXT NOT NULL,
                    codigo_produto TEXT UNIQUE,
                    descricao TEXT,
                    marca_id INTEGER,
                    quantidade_atual INTEGER NOT NULL DEFAULT 0,
                    localizacao TEXT, -- Novo campo para localização no estoque
                    FOREIGN KEY (marca_id) REFERENCES marcas(id) ON DELETE SET NULL
                )
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS fornecedores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE,
                    contato TEXT,
                    telefone TEXT,
                    email TEXT,
                    endereco TEXT
                )
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS compras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fornecedor_id INTEGER NOT NULL,
                    data_emissao TEXT NOT NULL,
                    data_entrega TEXT,
                    prazo_entrega TEXT,
                    subtotal REAL NOT NULL DEFAULT 0.0,
                    desconto REAL NOT NULL DEFAULT 0.0,
                    frete REAL NOT NULL DEFAULT 0.0,
                    total_final REAL NOT NULL DEFAULT 0.0,
                    observacao TEXT,
                    status_pagamento TEXT NOT NULL DEFAULT 'Pendente', -- Novo campo para status de pagamento da compra
                    FOREIGN KEY (fornecedor_id) REFERENCES fornecedores(id) ON DELETE CASCADE
                )
            """)
            # Adicionar a coluna status_pagamento se ela não existir (para compatibilidade com DBs existentes)
            self.cursor.execute("""
                PRAGMA table_info(compras);
            """)
            columns = [col[1] for col in self.cursor.fetchall()]
            if 'status_pagamento' not in columns:
                self.cursor.execute("""
                    ALTER TABLE compras ADD COLUMN status_pagamento TEXT NOT NULL DEFAULT 'Pendente';
                """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS itens_compra (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    compra_id INTEGER NOT NULL,
                    produto_id INTEGER NOT NULL,
                    quantidade INTEGER NOT NULL,
                    preco_unitario REAL NOT NULL,
                    FOREIGN KEY (compra_id) REFERENCES compras(id) ON DELETE CASCADE,
                    FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE CASCADE
                )
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS contas_a_pagar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    compra_id INTEGER NOT NULL,
                    data_vencimento TEXT NOT NULL,
                    valor REAL NOT NULL,
                    valor_pago REAL NOT NULL DEFAULT 0.0,
                    status TEXT NOT NULL DEFAULT 'Pendente', -- Pendente, Pago, Parcialmente Pago
                    FOREIGN KEY (compra_id) REFERENCES compras(id) ON DELETE CASCADE
                )
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS movimentacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    produto_id INTEGER,
                    tipo TEXT NOT NULL,
                    quantidade INTEGER NOT NULL,
                    data_hora TEXT NOT NULL,
                    observacao TEXT,
                    FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE CASCADE
                )
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS product_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    image_path TEXT NOT NULL,
                    FOREIGN KEY (product_id) REFERENCES produtos(id) ON DELETE CASCADE
                )
            """)
            self.conn.commit()
            self.logger.info("Tabelas do banco de dados verificadas/criadas com sucesso.")
        except sqlite3.Error as e:
            self.logger.critical(f"Erro ao criar tabelas: {e}", exc_info=True)
            print(f"Erro ao criar tabelas: {e}")

    def _add_initial_brands(self):
        initial_brands = [
            "Chevrolet", "Volkswagen", "Fiat", "Ford", "Hyundai",
            "Toyota", "Honda", "Renault", "Jeep", "Mercedes-Benz",
            "BMW", "Audi", "Nissan", "Kia", "Peugeot"
        ]
        for brand_name in initial_brands:
            try:
                self.cursor.execute("INSERT OR IGNORE INTO marcas (nome) VALUES (?)", (brand_name,))
            except sqlite3.Error as e:
                self.logger.warning(f"Erro ao adicionar marca inicial '{brand_name}': {e}")
                print(f"Erro ao adicionar marca inicial '{brand_name}': {e}")
        self.conn.commit()
        self.logger.info("Marcas iniciais adicionadas/verificadas.")

    def close(self):
        if self.conn:
            self.conn.close()
            self.logger.info("Conexão com o banco de dados fechada.")

    # Métodos para Marcas
    def add_marca(self, nome):
        try:
            self.cursor.execute("INSERT INTO marcas (nome) VALUES (?)", (nome,))
            self.conn.commit()
            self.logger.info(f"Marca '{nome}' adicionada com sucesso.")
            return True
        except sqlite3.IntegrityError:
            self.logger.warning(f"Tentativa de adicionar marca duplicada: '{nome}'.")
            print(f"Marca '{nome}' já existe.")
            return False
        except sqlite3.Error as e:
            self.logger.error(f"Erro ao adicionar marca '{nome}': {e}", exc_info=True)
            print(f"Erro ao adicionar marca: {e}")
            return False

    def update_marca(self, marca_id, novo_nome):
        try:
            self.cursor.execute("UPDATE marcas SET nome = ? WHERE id = ?", (novo_nome, marca_id))
            self.conn.commit()
            self.logger.info(f"Marca (ID: {marca_id}) atualizada para '{novo_nome}'.")
            return True
        except sqlite3.IntegrityError:
            self.logger.warning(f"Tentativa de atualizar marca para nome duplicado: '{novo_nome}'.")
            print(f"Marca '{novo_nome}' já existe.")
            return False
        except sqlite3.Error as e:
            self.logger.error(f"Erro ao atualizar marca (ID: {marca_id}) para '{novo_nome}': {e}", exc_info=True)
            print(f"Erro ao atualizar marca: {e}")
            return False

    def get_marcas(self):
        self.cursor.execute("SELECT id, nome FROM marcas ORDER BY nome")
        marcas = self.cursor.fetchall()
        self.logger.debug(f"Retornadas {len(marcas)} marcas.")
        return marcas

    def delete_marca(self, marca_id):
        try:
            self.cursor.execute("DELETE FROM marcas WHERE id = ?", (marca_id,))
            self.conn.commit()
            self.logger.info(f"Marca (ID: {marca_id}) deletada com sucesso.")
            return True
        except sqlite3.Error as e:
            self.logger.error(f"Erro ao deletar marca (ID: {marca_id}): {e}", exc_info=True)
            print(f"Erro ao deletar marca: {e}")
            return False

    def marca_has_products(self, marca_id):
        self.cursor.execute("SELECT COUNT(*) FROM produtos WHERE marca_id = ?", (marca_id,))
        count = self.cursor.fetchone()[0]
        self.logger.debug(f"Marca (ID: {marca_id}) tem {count} produtos associados.")
        return count > 0

    # Métodos para Fornecedores
    def add_fornecedor(self, nome, contato, telefone, email, endereco):
        try:
            self.cursor.execute(
                "INSERT INTO fornecedores (nome, contato, telefone, email, endereco) VALUES (?, ?, ?, ?, ?)",
                (nome, contato, telefone, email, endereco)
            )
            self.conn.commit()
            self.logger.info(f"Fornecedor '{nome}' adicionado com sucesso.")
            return True
        except sqlite3.IntegrityError:
            self.logger.warning(f"Tentativa de adicionar fornecedor duplicado: '{nome}'.")
            print(f"Fornecedor '{nome}' já existe.")
            return False
        except sqlite3.Error as e:
            self.logger.error(f"Erro ao adicionar fornecedor '{nome}': {e}", exc_info=True)
            print(f"Erro ao adicionar fornecedor: {e}")
            return False

    def get_fornecedores(self, search_term=""):
        query = "SELECT id, nome, contato, telefone, email, endereco FROM fornecedores WHERE nome LIKE ? ORDER BY nome"
        self.cursor.execute(query, (f"%{search_term}%",))
        return self.cursor.fetchall()

    def get_fornecedor_by_id(self, fornecedor_id):
        self.cursor.execute("SELECT id, nome, contato, telefone, email, endereco FROM fornecedores WHERE id = ?", (fornecedor_id,))
        return self.cursor.fetchone()

    def update_fornecedor(self, fornecedor_id, nome, contato, telefone, email, endereco):
        try:
            self.cursor.execute(
                """
                UPDATE fornecedores
                SET nome = ?, contato = ?, telefone = ?, email = ?, endereco = ?
                WHERE id = ?
                """,
                (nome, contato, telefone, email, endereco, fornecedor_id)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            print(f"Fornecedor '{nome}' já existe para outro registro.")
            return False
        except sqlite3.Error as e:
            print(f"Erro ao atualizar fornecedor: {e}")
            return False

    def delete_fornecedor(self, fornecedor_id):
        try:
            self.conn.execute("BEGIN TRANSACTION")
            
            self.cursor.execute("SELECT id FROM compras WHERE fornecedor_id = ?", (fornecedor_id,))
            compras_ids = [row[0] for row in self.cursor.fetchall()]
            
            for compra_id in compras_ids:
                self.cursor.execute("DELETE FROM itens_compra WHERE compra_id = ?", (compra_id,))
                self.cursor.execute("DELETE FROM contas_a_pagar WHERE compra_id = ?", (compra_id,))
            
            self.cursor.execute("DELETE FROM compras WHERE fornecedor_id = ?", (fornecedor_id,))
            self.cursor.execute("DELETE FROM fornecedores WHERE id = ?", (fornecedor_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"Erro ao deletar fornecedor: {e}")
            return False

    def fornecedor_has_compras(self, fornecedor_id):
        self.cursor.execute("SELECT COUNT(*) FROM compras WHERE fornecedor_id = ?", (fornecedor_id,))
        return self.cursor.fetchone()[0] > 0

    # Métodos para Produtos
    def add_produto(self, nome_produto, codigo_produto, descricao, marca_id, quantidade_inicial, localizacao):
        try:
            self.cursor.execute(
                "INSERT INTO produtos (nome_produto, codigo_produto, descricao, marca_id, quantidade_atual, localizacao) VALUES (?, ?, ?, ?, ?, ?)",
                (nome_produto, codigo_produto, descricao, marca_id, quantidade_inicial, localizacao)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            print(f"Produto com código '{codigo_produto}' já existe.")
            return False
        except sqlite3.Error as e:
            print(f"Erro ao adicionar produto: {e}")
            return False

    def update_produto(self, produto_id, nome_produto, codigo_produto, descricao, marca_id, quantidade_atual, localizacao):
        try:
            self.cursor.execute(
                """
                UPDATE produtos
                SET nome_produto = ?, codigo_produto = ?, descricao = ?, marca_id = ?, quantidade_atual = ?, localizacao = ?
                WHERE id = ?
                """,
                (nome_produto, codigo_produto, descricao, marca_id, quantidade_atual, localizacao, produto_id)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            print(f"Produto com código '{codigo_produto}' já existe para outro produto.")
            return False
        except sqlite3.Error as e:
            print(f"Erro ao atualizar produto: {e}")
            return False

    def get_produtos(self, search_term=""):
        query = """
            SELECT p.id, p.nome_produto, p.codigo_produto, m.nome, p.quantidade_atual, p.descricao, p.localizacao
            FROM produtos p
            LEFT JOIN marcas m ON p.marca_id = m.id
            WHERE p.nome_produto LIKE ? OR p.codigo_produto LIKE ?
            ORDER BY p.nome_produto
        """
        self.cursor.execute(query, (f"%{search_term}%", f"%{search_term}%"))
        return self.cursor.fetchall()

    def get_produto_by_id(self, produto_id):
        self.cursor.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
        return self.cursor.fetchone()

    def delete_produto(self, produto_id):
        try:
            self.conn.execute("BEGIN TRANSACTION")
            
            # 1. Obter caminhos das imagens associadas ao produto
            image_paths = self.get_product_images(produto_id)
            
            # 2. Excluir entradas relacionadas ao produto nas tabelas
            self.cursor.execute("DELETE FROM itens_compra WHERE produto_id = ?", (produto_id,))
            self.cursor.execute("DELETE FROM movimentacoes WHERE produto_id = ?", (produto_id,))
            self.cursor.execute("DELETE FROM product_images WHERE product_id = ?", (produto_id,))
            self.cursor.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
            
            self.conn.commit()
            self.logger.info(f"Produto (ID: {produto_id}) e suas referências no DB excluídos com sucesso.")

            # 3. Excluir arquivos de imagem do sistema de arquivos
            for path in image_paths:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                        self.logger.info(f"Imagem '{path}' excluída do sistema de arquivos.")
                        
                        # Tentar remover o diretório pai se estiver vazio
                        image_dir = os.path.dirname(path)
                        if os.path.exists(image_dir) and not os.listdir(image_dir):
                            try:
                                os.rmdir(image_dir)
                                self.logger.info(f"Diretório de imagens vazio '{image_dir}' excluído.")
                            except OSError as dir_error:
                                self.logger.error(f"Erro ao excluir diretório de imagem vazio '{image_dir}': {dir_error}", exc_info=True)
                    except OSError as file_error:
                        self.logger.error(f"Erro ao excluir arquivo de imagem '{path}': {file_error}", exc_info=True)
                        # Não faz rollback aqui, pois o DB já foi atualizado. Apenas loga o erro.
                else:
                    self.logger.warning(f"Tentativa de excluir imagem '{path}', mas o arquivo não foi encontrado.")

            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            self.logger.error(f"Erro ao deletar produto (ID: {produto_id}) do banco de dados: {e}", exc_info=True)
            print(f"Erro ao deletar produto: {e}")
            return False

    def produto_has_compras(self, produto_id):
        self.cursor.execute("SELECT COUNT(*) FROM itens_compra WHERE produto_id = ?", (produto_id,))
        return self.cursor.fetchone()[0] > 0

    def update_produto_quantity(self, produto_id, quantidade_movimentada, tipo_movimentacao, observacao="", foto_path=None):
        try:
            self.cursor.execute("SELECT quantidade_atual FROM produtos WHERE id = ?", (produto_id,))
            current_quantity = self.cursor.fetchone()[0]

            if tipo_movimentacao == "Entrada":
                new_quantity = current_quantity + quantidade_movimentada
            elif tipo_movimentacao == "Saída":
                if quantidade_movimentada > current_quantity:
                    return False # Saída maior que o estoque atual
                new_quantity = current_quantity - quantidade_movimentada
            else:
                return False # Tipo de movimentação inválido

            self.cursor.execute(
                "UPDATE produtos SET quantidade_atual = ? WHERE id = ?",
                (new_quantity, produto_id)
            )
            
            self.add_movimentacao(produto_id, tipo_movimentacao, quantidade_movimentada, observacao) # Removido foto_path
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Erro ao atualizar quantidade do produto: {e}")
            return False

    # Métodos para Compras
    def add_compra(self, fornecedor_id, data_emissao, data_entrega, prazo_entrega, subtotal, desconto, frete, total_final, observacao, status_pagamento='Pendente'):
        try:
            self.cursor.execute(
                """
                INSERT INTO compras (fornecedor_id, data_emissao, data_entrega, prazo_entrega, subtotal, desconto, frete, total_final, observacao, status_pagamento)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (fornecedor_id, data_emissao, data_entrega, prazo_entrega, subtotal, desconto, frete, total_final, observacao, status_pagamento)
            )
            self.conn.commit()
            return self.cursor.lastrowid # Retorna o ID da compra inserida
        except sqlite3.Error as e:
            print(f"Erro ao adicionar compra: {e}")
            return None

    def add_item_compra(self, compra_id, produto_id, quantidade, preco_unitario):
        try:
            self.cursor.execute(
                "INSERT INTO itens_compra (compra_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                (compra_id, produto_id, quantidade, preco_unitario)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Erro ao adicionar item de compra: {e}")
            return False

    def get_compras(self, search_term=""):
        query = """
            SELECT c.id, f.nome, c.data_emissao, c.total_final, c.status_pagamento
            FROM compras c
            JOIN fornecedores f ON c.fornecedor_id = f.id
            WHERE f.nome LIKE ? OR c.data_emissao LIKE ? OR c.status_pagamento LIKE ?
            ORDER BY c.data_emissao DESC
        """
        self.cursor.execute(query, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
        return self.cursor.fetchall()

    def get_compra_details(self, compra_id):
        self.cursor.execute(
            """
            SELECT c.id, f.nome, c.data_emissao, c.data_entrega, c.prazo_entrega,
                   c.subtotal, c.desconto, c.frete, c.total_final, c.observacao, c.status_pagamento
            FROM compras c
            JOIN fornecedores f ON c.fornecedor_id = f.id
            WHERE c.id = ?
            """,
            (compra_id,)
        )
        compra = self.cursor.fetchone()

        self.cursor.execute(
            """
            SELECT ic.produto_id, p.nome_produto, ic.quantidade, ic.preco_unitario
            FROM itens_compra ic
            JOIN produtos p ON ic.produto_id = p.id
            WHERE ic.compra_id = ?
            """,
            (compra_id,)
        )
        itens = self.cursor.fetchall()
        return compra, itens

    def update_compra(self, compra_id, fornecedor_id, data_emissao, data_entrega, prazo_entrega, subtotal, desconto, frete, total_final, observacao, status_pagamento, itens_compra_data):
        try:
            self.conn.execute("BEGIN TRANSACTION")

            # 1. Atualizar a compra principal
            self.cursor.execute(
                """
                UPDATE compras
                SET fornecedor_id = ?, data_emissao = ?, data_entrega = ?, prazo_entrega = ?,
                    subtotal = ?, desconto = ?, frete = ?, total_final = ?, observacao = ?, status_pagamento = ?
                WHERE id = ?
                """,
                (fornecedor_id, data_emissao, data_entrega, prazo_entrega,
                 subtotal, desconto, frete, total_final, observacao, status_pagamento, compra_id)
            )

            # 2. Excluir todos os itens de compra existentes para esta compra
            self.cursor.execute("DELETE FROM itens_compra WHERE compra_id = ?", (compra_id,))

            # 3. Inserir os novos itens de compra
            for item_data in itens_compra_data:
                produto_id = item_data['produto_id']
                quantidade = item_data['quantidade']
                preco_unitario = item_data['preco_unitario']
                self.cursor.execute(
                    "INSERT INTO itens_compra (compra_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                    (compra_id, produto_id, quantidade, preco_unitario)
                )
            
            # 4. Atualizar a conta a pagar associada (se houver)
            # Simplificado: assume que há uma conta a pagar por compra e a atualiza
            self.cursor.execute(
                """
                UPDATE contas_a_pagar
                SET data_vencimento = ?, valor = ?
                WHERE compra_id = ?
                """,
                (data_entrega, total_final, compra_id) # Usando data_entrega como nova data de vencimento e total_final como novo valor
            )

            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"Erro ao atualizar compra: {e}")
            return False

    def delete_compra(self, compra_id):
        try:
            self.cursor.execute("DELETE FROM compras WHERE id = ?", (compra_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Erro ao deletar compra: {e}")
            return False

    # Métodos para Contas a Pagar
    def delete_conta_a_pagar(self, conta_id):
        try:
            self.cursor.execute("DELETE FROM contas_a_pagar WHERE id = ?", (conta_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Erro ao deletar conta a pagar: {e}")
            return False

    def add_conta_a_pagar(self, compra_id, data_vencimento, valor, valor_pago=0.0, status='Pendente'):
        try:
            self.cursor.execute(
                """
                INSERT INTO contas_a_pagar (compra_id, data_vencimento, valor, valor_pago, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (compra_id, data_vencimento, valor, valor_pago, status)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Erro ao adicionar conta a pagar: {e}")
            return False

    def get_contas_a_pagar(self, search_term=""):
        query = """
            SELECT cap.id, f.nome, c.data_emissao, cap.data_vencimento, cap.valor, cap.valor_pago, cap.status
            FROM contas_a_pagar cap
            JOIN compras c ON cap.compra_id = c.id
            JOIN fornecedores f ON c.fornecedor_id = f.id
            WHERE f.nome LIKE ? OR cap.data_vencimento LIKE ? OR cap.status LIKE ?
            ORDER BY cap.data_vencimento ASC
        """
        self.cursor.execute(query, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
        return self.cursor.fetchall()

    def update_conta_a_pagar_status(self, conta_id, valor_pago, status):
        try:
            self.cursor.execute(
                "UPDATE contas_a_pagar SET valor_pago = ?, status = ? WHERE id = ?",
                (valor_pago, status, conta_id)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Erro ao atualizar status da conta a pagar: {e}")
            return False

    # Métodos para Movimentações
    def add_movimentacao(self, produto_id, tipo, quantidade, observacao=""):
        data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            self.cursor.execute(
                "INSERT INTO movimentacoes (produto_id, tipo, quantidade, data_hora, observacao) VALUES (?, ?, ?, ?, ?)",
                (produto_id, tipo, quantidade, data_hora, observacao)
            )
            # Não commita aqui, pois a movimentação é parte da atualização do produto
            return True
        except sqlite3.Error as e:
            print(f"Erro ao registrar movimentação: {e}")
            return False

    def get_movimentacoes_by_product(self, produto_id):
        self.cursor.execute(
            "SELECT tipo, quantidade, data_hora, observacao FROM movimentacoes WHERE produto_id = ? ORDER BY data_hora DESC",
            (produto_id,)
        )
        return self.cursor.fetchall()

    # Métodos para Imagens de Produtos
    def add_product_image(self, product_id, image_path):
        try:
            self.cursor.execute("INSERT INTO product_images (product_id, image_path) VALUES (?, ?)", (product_id, image_path))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Erro ao adicionar imagem do produto: {e}")
            return False

    def get_product_images(self, product_id):
        self.cursor.execute("SELECT image_path FROM product_images WHERE product_id = ?", (product_id,))
        return [row[0] for row in self.cursor.fetchall()]

    def delete_product_images(self, product_id):
        try:
            self.cursor.execute("DELETE FROM product_images WHERE product_id = ?", (product_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Erro ao deletar imagens do produto: {e}")
            return False

    def get_movimentacoes_by_product(self, produto_id):
        self.cursor.execute(
            "SELECT tipo, quantidade, data_hora, observacao FROM movimentacoes WHERE produto_id = ? ORDER BY data_hora DESC",
            (produto_id,)
        )
        return self.cursor.fetchall()

    def get_all_products_for_combobox(self):
        self.cursor.execute("SELECT id, nome_produto, codigo_produto FROM produtos ORDER BY nome_produto")
        return self.cursor.fetchall()

    # Métodos para Estatísticas do Dashboard
    def get_total_products_count(self):
        self.cursor.execute("SELECT COUNT(*) FROM produtos")
        return self.cursor.fetchone()[0]

    def get_low_stock_products_count(self, low_stock_threshold=10):
        self.cursor.execute("SELECT COUNT(*) FROM produtos WHERE quantidade_atual <= ?", (low_stock_threshold,))
        return self.cursor.fetchone()[0]

    def get_total_brands_count(self):
        self.cursor.execute("SELECT COUNT(*) FROM marcas")
        return self.cursor.fetchone()[0]

    def get_all_fornecedores_for_combobox(self):
        self.cursor.execute("SELECT id, nome FROM fornecedores ORDER BY nome")
        return self.cursor.fetchall()
