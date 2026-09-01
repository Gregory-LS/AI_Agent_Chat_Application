'''OpenRouter metadata capture and storage.'''

from .capture import extract_metadata
from .storage import MetadataStore, store_response

__all__ = ['extract_metadata', 'MetadataStore', 'store_response']
__version__ = '0.1.0'
