"""Loader that loads data from JSON."""
import json
from pathlib import Path
from typing import Callable, Dict, List, Optional, Union

from langchain.docstore.document import Document
from langchain.document_loaders.base import BaseLoader


class JSONLoader(BaseLoader):
    def __init__(
        self,
        file_path: Union[str, Path],
        content_key: Optional[str] = None,
        ):
        self.file_path = Path(file_path).resolve()
        self._content_key = content_key
        
    def load(self) -> List[Document]:
        """Load and return documents from the JSON file."""

        docs=[]
        # Load JSON file
        with open(self.file_path, encoding="utf8") as file:
            data = json.load(file)

            metadata = dict(
                source=self.file_path.name,
                title=data.get('title', ''),  # Use get() to handle missing 'title' key gracefully
                date=data.get('createdTimestampUsec', ''),  # Use get() to handle missing 'createdTimestampUsec' key gracefully
            )

            docs.append(Document(page_content=data.get('textContent', ''), metadata=metadata))
        return docs