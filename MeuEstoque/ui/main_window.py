import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QLabel,
    QMessageBox, QHeaderView, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap # Adicionado QPixmap para exibir imagens

from MeuEstoque.database.database_manager import DatabaseManager
from MeuEstoque.ui.add_product_window import AddProductWindow
from MeuEstoque.ui.move_stock_window import MoveStockWindow
from MeuEstoque.ui.manage_brands_window import ManageBrandsWindow
from MeuEstoque.ui.product_details_window import ProductDetailsWindow # Adicionado ProductDetailsWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MeuEstoque - Sistema de Gestão de Estoque")
        self.setGeometry(100, 100, 1000, 600)

        self.db = DatabaseManager()

        self.setStyleSheet(open("MeuEstoque/ui/styles.qss").read())

        self._setup_ui()
        self._load_products()

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Layout de busca
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar produto por nome ou código...")
        self.search_input.textChanged.connect(self._load_products)
        search_layout.addWidget(QLabel("Buscar:"))
        search_layout.addWidget(self.search_input)
        main_layout.addLayout(search_layout)

        # Tabela de produtos
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(6) # Adicionar uma coluna para Localização
        self.product_table.setHorizontalHeaderLabels(["ID", "Nome do Produto", "Código", "Marca", "Quantidade Atual", "Localização"])
        self.product_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.product_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.product_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers) # Não permitir edição direta
        self.product_table.doubleClicked.connect(self._show_product_details) # Adicionado double click para detalhes
        main_layout.addWidget(self.product_table)

        # Layout de botões
        button_layout = QHBoxLayout()
        self.add_product_btn = QPushButton("Adicionar Produto")
        self.add_product_btn.clicked.connect(self._open_add_product_window)
        button_layout.addWidget(self.add_product_btn)

        self.move_stock_btn = QPushButton("Registrar Entrada/Saída")
        self.move_stock_btn.clicked.connect(self._open_move_stock_window)
        button_layout.addWidget(self.move_stock_btn)

        self.manage_brands_btn = QPushButton("Gerenciar Marcas")
        self.manage_brands_btn.clicked.connect(self._open_manage_brands_window)
        button_layout.addWidget(self.manage_brands_btn)

        self.delete_product_btn = QPushButton("Excluir Produto")
        self.delete_product_btn.clicked.connect(self._delete_selected_product)
        self.delete_product_btn.setEnabled(False) # Desabilitado inicialmente
        self.product_table.itemSelectionChanged.connect(self._toggle_delete_product_button)
        button_layout.addWidget(self.delete_product_btn)
        
        main_layout.addLayout(button_layout)

        # Dashboard de Estatísticas
        dashboard_group = QGroupBox("Estatísticas do Estoque")
        dashboard_layout = QHBoxLayout(dashboard_group)

        self.total_products_label = QLabel("Total de Produtos: 0")
        self.low_stock_label = QLabel("Estoque Baixo: 0")
        self.total_brands_label = QLabel("Total de Marcas: 0")

        dashboard_layout.addWidget(self.total_products_label)
        dashboard_layout.addWidget(self.low_stock_label)
        dashboard_layout.addWidget(self.total_brands_label)
        main_layout.addWidget(dashboard_group)

        # Botão de Atualização
        refresh_button = QPushButton("Atualizar Dados")
        refresh_button.clicked.connect(self._load_all_data)
        main_layout.addWidget(refresh_button)

    def _load_all_data(self):
        self._load_products()
        self._load_dashboard_stats()

    def _load_products(self):
        search_term = self.search_input.text()
        products = self.db.get_produtos(search_term)
        self.product_table.setRowCount(len(products))

        for row_idx, product in enumerate(products):
            # product agora tem 7 elementos: id, nome_produto, codigo_produto, nome_marca, quantidade_atual, descricao, localizacao
            self.product_table.setItem(row_idx, 0, QTableWidgetItem(str(product[0]))) # ID
            self.product_table.setItem(row_idx, 1, QTableWidgetItem(product[1])) # Nome do Produto
            self.product_table.setItem(row_idx, 2, QTableWidgetItem(product[2] if product[2] else 'N/A')) # Código
            self.product_table.setItem(row_idx, 3, QTableWidgetItem(product[3] if product[3] else 'Sem Marca')) # Marca
            self.product_table.setItem(row_idx, 4, QTableWidgetItem(str(product[4]))) # Quantidade Atual
            self.product_table.setItem(row_idx, 5, QTableWidgetItem(product[6] if product[6] else 'N/A')) # Localização

    def _show_product_details(self, index):
        row = index.row()
        product_id = int(self.product_table.item(row, 0).text())
        
        details_window = ProductDetailsWindow(self.db, product_id, self)
        details_window.exec()

    def _load_dashboard_stats(self):
        total_products = self.db.get_total_products_count()
        low_stock_products = self.db.get_low_stock_products_count()
        total_brands = self.db.get_total_brands_count()

        self.total_products_label.setText(f"Total de Produtos: {total_products}")
        self.low_stock_label.setText(f"Estoque Baixo: {low_stock_products}")
        self.total_brands_label.setText(f"Total de Marcas: {total_brands}")

    def _open_add_product_window(self):
        self.add_product_win = AddProductWindow(self.db, self)
        self.add_product_win.product_added.connect(self._load_products)
        self.add_product_win.exec()

    def _open_move_stock_window(self):
        self.move_stock_win = MoveStockWindow(self.db, self)
        self.move_stock_win.stock_moved.connect(self._load_products)
        self.move_stock_win.exec()

    def _open_manage_brands_window(self):
        self.manage_brands_win = ManageBrandsWindow(self.db, self)
        self.manage_brands_win.brands_updated.connect(self._load_products) # Atualiza produtos caso marcas sejam alteradas
        self.manage_brands_win.exec()

    def _toggle_delete_product_button(self):
        self.delete_product_btn.setEnabled(self.product_table.currentItem() is not None)

    def _delete_selected_product(self):
        selected_items = self.product_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Atenção", "Por favor, selecione um produto para excluir.")
            return

        row = selected_items[0].row()
        product_id = int(self.product_table.item(row, 0).text())
        product_name = self.product_table.item(row, 1).text()

        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Tem certeza que deseja excluir o produto '{product_name}'? Todas as movimentações associadas também serão excluídas.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_produto(product_id):
                QMessageBox.information(self, "Sucesso", f"Produto '{product_name}' excluído com sucesso!")
                self._load_products() # Recarregar a tabela após a exclusão
            else:
                QMessageBox.critical(self, "Erro", f"Não foi possível excluir o produto '{product_name}'.")

    def closeEvent(self, event):
        self.db.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
