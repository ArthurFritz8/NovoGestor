import unittest
import os
import sqlite3
from MeuEstoque.database.database_manager import DatabaseManager

class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        self.db_name = "test_estoque.db"
        if os.path.exists(self.db_name):
            os.remove(self.db_name)
        self.db_manager = DatabaseManager(self.db_name)

    def tearDown(self):
        self.db_manager.close()
        if os.path.exists(self.db_name):
            os.remove(self.db_name)

    def test_add_marca(self):
        self.assertTrue(self.db_manager.add_marca("Marca Teste"))
        marcas = self.db_manager.get_marcas()
        self.assertTrue(any(marca[1] == "Marca Teste" for marca in marcas))

    def test_add_duplicate_marca(self):
        self.db_manager.add_marca("Marca Duplicada")
        self.assertFalse(self.db_manager.add_marca("Marca Duplicada"))

    def test_update_marca(self):
        self.db_manager.add_marca("Marca Antiga")
        marcas = self.db_manager.get_marcas()
        marca_id = marcas[0][0]
        self.assertTrue(self.db_manager.update_marca(marca_id, "Marca Nova"))
        marcas_atualizadas = self.db_manager.get_marcas()
        self.assertTrue(any(marca[0] == marca_id and marca[1] == "Marca Nova" for marca in marcas_atualizadas))

    def test_delete_marca(self):
        self.db_manager.add_marca("Marca para Deletar")
        marcas = self.db_manager.get_marcas()
        marca_id = marcas[0][0]
        self.assertTrue(self.db_manager.delete_marca(marca_id))
        marcas_restantes = self.db_manager.get_marcas()
        self.assertFalse(any(marca[0] == marca_id for marca in marcas_restantes))

    def test_add_fornecedor(self):
        self.assertTrue(self.db_manager.add_fornecedor("Fornecedor Teste", "Contato Teste", "11999999999", "teste@email.com", "Rua Teste"))
        fornecedores = self.db_manager.get_fornecedores()
        self.assertEqual(len(fornecedores), 1)
        self.assertEqual(fornecedores[0][1], "Fornecedor Teste")

    def test_add_produto(self):
        self.db_manager.add_marca("Marca Produto")
        marcas = self.db_manager.get_marcas()
        marca_id = marcas[0][0]
        self.assertTrue(self.db_manager.add_produto("Produto Teste", "COD001", "Descrição", marca_id, 10, "A1"))
        produtos = self.db_manager.get_produtos()
        self.assertEqual(len(produtos), 1)
        self.assertEqual(produtos[0][1], "Produto Teste")

    def test_update_produto_quantity_entrada(self):
        self.db_manager.add_marca("Marca Qty")
        marcas = self.db_manager.get_marcas()
        marca_id = marcas[0][0]
        self.db_manager.add_produto("Produto Qty", "COD002", "Descrição", marca_id, 10, "B2")
        produtos = self.db_manager.get_produtos()
        produto_id = produtos[0][0]

        self.assertTrue(self.db_manager.update_produto_quantity(produto_id, 5, "Entrada"))
        produto_atualizado = self.db_manager.get_produto_by_id(produto_id)
        self.assertEqual(produto_atualizado[5], 15) # Quantidade atualizada

    def test_update_produto_quantity_saida(self):
        self.db_manager.add_marca("Marca Qty Saida")
        marcas = self.db_manager.get_marcas()
        marca_id = marcas[0][0]
        self.db_manager.add_produto("Produto Qty Saida", "COD003", "Descrição", marca_id, 10, "C3")
        produtos = self.db_manager.get_produtos()
        produto_id = produtos[0][0]

        self.assertTrue(self.db_manager.update_produto_quantity(produto_id, 3, "Saída"))
        produto_atualizado = self.db_manager.get_produto_by_id(produto_id)
        self.assertEqual(produto_atualizado[5], 7) # Quantidade atualizada

    def test_update_produto_quantity_saida_insuficiente(self):
        self.db_manager.add_marca("Marca Qty Insuficiente")
        marcas = self.db_manager.get_marcas()
        marca_id = marcas[0][0]
        self.db_manager.add_produto("Produto Qty Insuficiente", "COD004", "Descrição", marca_id, 5, "D4")
        produtos = self.db_manager.get_produtos()
        produto_id = produtos[0][0]

        self.assertFalse(self.db_manager.update_produto_quantity(produto_id, 10, "Saída"))
        produto_atualizado = self.db_manager.get_produto_by_id(produto_id)
        self.assertEqual(produto_atualizado[5], 5) # Quantidade não deve mudar

    def test_delete_produto_deletes_images(self):
        # 1. Create a dummy image file
        image_dir = os.path.join("MeuEstoque", "product_images", "test_product")
        os.makedirs(image_dir, exist_ok=True)
        dummy_image_path = os.path.join(image_dir, "dummy_image.jpg")
        with open(dummy_image_path, "w") as f:
            f.write("dummy image content")
        self.assertTrue(os.path.exists(dummy_image_path))

        # 2. Add a product and associate the image
        self.db_manager.add_marca("Marca Imagem")
        marcas = self.db_manager.get_marcas()
        marca_id = marcas[0][0]
        self.db_manager.add_produto("Produto com Imagem", "IMG001", "Descrição", marca_id, 5, "E5")
        produtos = self.db_manager.get_produtos()
        produto_id = produtos[0][0]
        self.db_manager.add_product_image(produto_id, dummy_image_path)

        # 3. Verify image file exists
        self.assertTrue(os.path.exists(dummy_image_path))

        # 4. Delete the product
        self.assertTrue(self.db_manager.delete_produto(produto_id))

        # 5. Verify image file no longer exists
        self.assertFalse(os.path.exists(dummy_image_path))
        
        # 5. Verify image file no longer exists
        self.assertFalse(os.path.exists(dummy_image_path))
        
        # 6. Verify the parent directory is also removed if it's empty
        self.assertFalse(os.path.exists(image_dir))

if __name__ == '__main__':
    unittest.main()
