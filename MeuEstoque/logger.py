import logging
import os
from datetime import datetime

# Define o diretório de logs
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Define o nome do arquivo de log com a data atual
LOG_FILENAME = datetime.now().strftime("app_%Y-%m-%d.log")
LOG_FILEPATH = os.path.join(LOG_DIR, LOG_FILENAME)

# Configuração básica do logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILEPATH),
        logging.StreamHandler() # Para exibir logs no console também
    ]
)

def get_logger(name):
    """
    Retorna um logger configurado para uso em módulos específicos.
    """
    return logging.getLogger(name)

# Exemplo de uso:
# logger = get_logger(__name__)
# logger.info("Aplicação iniciada.")
