"""Listed info client interface."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class ListedInfoClientInterface(ABC):
    """Interface for fetching listed company information."""

    @abstractmethod
    async def get_listed_info(
        self, code: Optional[str] = None, date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get listed company information.

        Args:
            code: Stock code (4-10 characters). If None, get all stocks.
            date: Target date in YYYYMMDD format. If None, get latest data.

        Returns:
            List of listed company information dictionaries.

        Raises:
            JQuantsListedInfoAPIError: If API request fails.
            ValidationError: If response data is invalid.
        """
        pass

    @abstractmethod
    async def get_all_listed_info(
        self, date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all listed company information with pagination support.

        Args:
            date: Target date in YYYYMMDD format. If None, get latest data.

        Returns:
            List of all listed company information dictionaries.

        Raises:
            JQuantsListedInfoAPIError: If API request fails.
            ValidationError: If response data is invalid.
        """
        pass