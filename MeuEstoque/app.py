import sys
import os
from PyQt6.QtWidgets import QApplication

# Adiciona o diretório raiz do projeto ao sys.path para resolver imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from MeuEstoque.ui.main_window import MainWindow
from MeuEstoque.database.database_manager import DatabaseManager
from MeuEstoque.logger import get_logger

logger = get_logger(__name__)

if __name__ == "__main__":
    try:
        # Garante que o diretório de imagens do produto exista
        app_dir = os.path.dirname(os.path.abspath(__file__))
        images_base_dir = os.path.join(app_dir, "product_images")
        os.makedirs(images_base_dir, exist_ok=True)
        logger.info(f"Diretório base de imagens garantido: {images_base_dir}")

        # Garante que o banco de dados seja inicializado e as tabelas criadas
        # antes de iniciar a aplicação.
        db_manager = DatabaseManager()
        db_manager.close() # Fecha a conexão inicial, a MainWindow abrirá a sua própria.
        logger.info("Banco de dados inicializado e tabelas verificadas.")

        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        logger.critical(f"Erro fatal na inicialização da aplicação: {e}", exc_info=True)
        sys.exit(1)
