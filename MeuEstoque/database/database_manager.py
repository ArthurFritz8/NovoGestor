import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name="estoque.db"):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_tables()
        self._add_initial_brands()

    def _connect(self):
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
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
        except sqlite3.Error as e:
            print(f"Erro ao criar tabelas: {e}")

    def _add_initial_brands(self):
        initial_brands = [
            "Chevrolet", "Volkswagen", "Fiat", "Ford", "Hyundai",
            "Toyota", "Honda", "Renault", "Jeep", "Mercedes-Benz",
            "BMW", "Audi", "Nissan", "Kia", "Peugeot"
        ]
        # Limpa as marcas existentes antes de adicionar as novas, se o banco de dados estiver vazio
        self.cursor.execute("DELETE FROM marcas WHERE id NOT IN (SELECT marca_id FROM produtos WHERE marca_id IS NOT NULL)")
        for brand_name in initial_brands:
            try:
                self.cursor.execute("INSERT OR IGNORE INTO marcas (nome) VALUES (?)", (brand_name,))
            except sqlite3.Error as e:
                print(f"Erro ao adicionar marca inicial '{brand_name}': {e}")
        self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()

    # Métodos para Marcas
    def add_marca(self, nome):
        try:
            self.cursor.execute("INSERT INTO marcas (nome) VALUES (?)", (nome,))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            print(f"Marca '{nome}' já existe.")
            return False
        except sqlite3.Error as e:
            print(f"Erro ao adicionar marca: {e}")
            return False

    def get_marcas(self):
        self.cursor.execute("SELECT id, nome FROM marcas ORDER BY nome")
        return self.cursor.fetchall()

    def delete_marca(self, marca_id):
        try:
            self.cursor.execute("DELETE FROM marcas WHERE id = ?", (marca_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Erro ao deletar marca: {e}")
            return False

    def marca_has_products(self, marca_id):
        self.cursor.execute("SELECT COUNT(*) FROM produtos WHERE marca_id = ?", (marca_id,))
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
            self.cursor.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Erro ao deletar produto: {e}")
            return False

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
