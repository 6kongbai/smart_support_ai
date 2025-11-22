from loguru import logger

from app.db.milvus.client import client


def remove_milvus_collection(collection_name: str):
    if client.has_collection(collection_name):
        try:
            client.drop_collection(collection_name)
            logger.info(f"Collection '{collection_name}' dropped.")
        except Exception as e:
            logger.error(f"Error dropping collection '{collection_name}': {e}")
    else:
        logger.error(f"Collection '{collection_name}' does not exist.")


