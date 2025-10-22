import sys
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox,
    QGridLayout, QGroupBox, QSizePolicy, QApplication, QStyle
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QImage, QIcon

from MeuEstoque.database.database_manager import DatabaseManager
from MeuEstoque.logger import get_logger

logger = get_logger(__name__)

class ProductDetailsWindow(QDialog):
    def __init__(self, db_manager, product_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Detalhes do Produto e Imagens")
        self.db = db_manager
        self.product_id = product_id
        self.image_paths = []
        self.current_image_index = 0
        self.setStyleSheet(open("MeuEstoque/ui/styles.qss").read())
        
        self._setup_ui()
        self._load_product_details()
        self._load_product_images() # This will now also call _display_current_image

        # Centralizar e redimensionar a janela dinamicamente
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        
        # Definir um tamanho ideal (ex: 70% da largura e 80% da altura da tela disponível)
        target_width = int(screen_geometry.width() * 0.7)
        target_height = int(screen_geometry.height() * 0.8)
        
        # Garantir um tamanho mínimo para a janela
        min_width = 800
        min_height = 600
        
        # Aplicar o tamanho final, respeitando o mínimo e o máximo da tela
        final_width = max(min_width, min(target_width, screen_geometry.width()))
        final_height = max(min_height, min(target_height, screen_geometry.height()))

        self.resize(final_width, final_height)
        
        # Centralizar a janela na tela
        self.move(screen_geometry.center() - self.rect().center())
        
        # Definir o tamanho mínimo e máximo para evitar que a janela exceda a tela ou fique muito pequena
        self.setMinimumSize(min_width, min_height)
        self.setMaximumSize(screen_geometry.width(), screen_geometry.height())

    def resizeEvent(self, event):
        # Redimensionar a imagem quando a janela for redimensionada
        self._display_current_image()
        super().resizeEvent(event)

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

        # Layout para a imagem principal e botões de navegação
        image_display_layout = QHBoxLayout()

        self.prev_button = QPushButton("")
        self.prev_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack))
        self.prev_button.setFixedSize(32, 32)
        self.prev_button.clicked.connect(self._previous_image)
        image_display_layout.addWidget(self.prev_button)

        self.image_label = QLabel("Nenhuma imagem disponível.")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        image_display_layout.addWidget(self.image_label)

        self.next_button = QPushButton("")
        self.next_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowForward))
        self.next_button.setFixedSize(32, 32)
        self.next_button.clicked.connect(self._next_image)
        image_display_layout.addWidget(self.next_button)

        images_layout.addLayout(image_display_layout)
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
            logger.warning(f"Produto com ID {self.product_id} não encontrado.")
            QMessageBox.warning(self, "Erro", "Produto não encontrado.")
            self.accept()

    def _load_product_images(self):
        self.image_paths = self.db.get_product_images(self.product_id)
        self.current_image_index = 0
        self._display_current_image()

    def _display_current_image(self):
        if not self.image_paths:
            self.image_label.setText("Nenhuma imagem disponível.")
            self.prev_button.hide()
            self.next_button.hide()
            return

        current_path = self.image_paths[self.current_image_index]
        logger.info(f"Tentando carregar imagem: {current_path}")

        if os.path.exists(current_path):
            pixmap = QPixmap(current_path)
            if not pixmap.isNull():
                # Escalar a imagem para caber no QLabel, mantendo a proporção
                scaled_pixmap = pixmap.scaled(
                    self.image_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
                self.image_label.setText("") # Limpa o texto se a imagem for carregada
                logger.info(f"Imagem carregada com sucesso: {current_path}")
            else:
                self.image_label.setText(f"Erro ao carregar imagem: {os.path.basename(current_path)}")
                logger.error(f"Erro ao carregar imagem (QPixmap is null): {current_path}")
        else:
            self.image_label.setText(f"Arquivo não encontrado: {os.path.basename(current_path)}")
            logger.warning(f"Erro: Arquivo de imagem não encontrado no caminho: {current_path}")
        
        self._update_navigation_buttons()

    def _update_navigation_buttons(self):
        if len(self.image_paths) > 1:
            self.prev_button.setVisible(True)
            self.next_button.setVisible(True)
            self.prev_button.setEnabled(self.current_image_index > 0)
            self.next_button.setEnabled(self.current_image_index < len(self.image_paths) - 1)
        else:
            self.prev_button.hide()
            self.next_button.hide()

    def _next_image(self):
        if self.current_image_index < len(self.image_paths) - 1:
            self.current_image_index += 1
            self._display_current_image()

    def _previous_image(self):
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self._display_current_image()
