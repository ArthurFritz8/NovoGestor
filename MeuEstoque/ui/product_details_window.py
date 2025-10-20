import sys
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QScrollArea, QWidget, QSizePolicy, QPushButton, QMessageBox,
    QGridLayout, QGroupBox # Adicionado QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QImage

from MeuEstoque.database.database_manager import DatabaseManager

class ProductDetailsWindow(QDialog):
    def __init__(self, db_manager, product_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Detalhes do Produto e Imagens")
        self.setGeometry(100, 100, 900, 700)
        self.db = db_manager
        self.product_id = product_id
        self.setStyleSheet(open("MeuEstoque/ui/styles.qss").read())
        self._setup_ui()
        self._load_product_details()
        self._load_product_images()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Seção de Detalhes do Produto
        details_group = QGroupBox("Detalhes do Produto")
        details_layout = QVBoxLayout(details_group)
        self.product_name_label = QLabel("Nome do Produto: ")
        self.product_code_label = QLabel("Código: ")
        self.product_desc_label = QLabel("Descrição: ")
        self.product_brand_label = QLabel("Marca: ")
        self.product_qty_label = QLabel("Quantidade Atual: ")
        self.product_location_label = QLabel("Localização: ")

        details_layout.addWidget(self.product_name_label)
        details_layout.addWidget(self.product_code_label)
        details_layout.addWidget(self.product_desc_label)
        details_layout.addWidget(self.product_brand_label)
        details_layout.addWidget(self.product_qty_label)
        details_layout.addWidget(self.product_location_label)
        main_layout.addWidget(details_group)

        # Seção de Imagens do Produto
        images_group = QGroupBox("Imagens do Produto")
        images_layout = QVBoxLayout(images_group)

        self.image_scroll_area = QScrollArea()
        self.image_scroll_area.setWidgetResizable(True)
        self.image_grid_widget = QWidget()
        self.image_grid_layout = QGridLayout(self.image_grid_widget)
        self.image_scroll_area.setWidget(self.image_grid_widget)
        images_layout.addWidget(self.image_scroll_area)
        main_layout.addWidget(images_group)

        # Botão Fechar
        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.accept)
        main_layout.addWidget(close_btn)

    def _load_product_details(self):
        product = self.db.get_produto_by_id(self.product_id)
        if product:
            # product: id, nome_produto, codigo_produto, descricao, marca_id, quantidade_atual, localizacao
            marca_id = product[4]
            marca_nome = "N/A"
            if marca_id:
                marcas = self.db.get_marcas()
                for mid, mname in marcas:
                    if mid == marca_id:
                        marca_nome = mname
                        break

            self.product_name_label.setText(f"Nome do Produto: {product[1]}")
            self.product_code_label.setText(f"Código: {product[2] if product[2] else 'N/A'}")
            self.product_desc_label.setText(f"Descrição: {product[3] if product[3] else 'N/A'}")
            self.product_brand_label.setText(f"Marca: {marca_nome}")
            self.product_qty_label.setText(f"Quantidade Atual: {product[5]}")
            self.product_location_label.setText(f"Localização: {product[6] if product[6] else 'N/A'}")
        else:
            QMessageBox.warning(self, "Erro", "Produto não encontrado.")
            self.accept()

    def _load_product_images(self):
        # Limpar previews existentes
        for i in reversed(range(self.image_grid_layout.count())): 
            widget = self.image_grid_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        image_paths = self.db.get_product_images(self.product_id)
        thumbnail_size = 150 # Tamanho maior para visualização
        
        if not image_paths:
            no_image_label = QLabel("Nenhuma imagem disponível para este produto.")
            no_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.image_grid_layout.addWidget(no_image_label, 0, 0)
            return

        for i, path in enumerate(image_paths):
            print(f"Tentando carregar imagem: {path}") # Depuração
            sys.stdout.flush()
            if os.path.exists(path):
                pixmap = QPixmap(path)
                if not pixmap.isNull():
                    thumbnail = pixmap.scaled(thumbnail_size, thumbnail_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    label = QLabel()
                    label.setPixmap(thumbnail)
                    label.setFixedSize(thumbnail_size, thumbnail_size)
                    label.setAlignment(int(Qt.AlignmentFlag.AlignCenter)) # Usar int() cast para consistência
                    self.image_grid_layout.addWidget(label, i // 3, i % 3) # 3 miniaturas por linha
                    print(f"Imagem carregada com sucesso: {path}")
                    sys.stdout.flush()
                else:
                    print(f"Erro ao carregar imagem (QPixmap is null): {path}")
                    sys.stdout.flush()
            else:
                print(f"Erro: Arquivo de imagem não encontrado no caminho: {path}")
                sys.stdout.flush()
