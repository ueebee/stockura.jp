"""Mapper for J-Quants listed info API responses."""
from datetime import datetime
from typing import List, Optional

from app.application.dtos.listed_info_dto import ListedInfoDTO
from app.infrastructure.external_services.jquants.types.responses import JQuantsListedInfoResponse


class JQuantsListedInfoMapper:
    """Maps J-Quants API responses to application DTOs."""
    
    @staticmethod
    def to_dto(response: JQuantsListedInfoResponse) -> ListedInfoDTO:
        """Convert J-Quants response to ListedInfoDTO.
        
        Args:
            response: J-Quants listed info response
            
        Returns:
            ListedInfoDTO instance
        """
        # 日付フォーマットの変換 (YYYY-MM-DD to YYYYMMDD)
        date_str = response["Date"].replace("-", "")
        
        return ListedInfoDTO(
            date=date_str,
            code=response["Code"],
            company_name=response["CompanyName"],
            company_name_english=response.get("CompanyNameEnglish"),
            sector_17_code=response["Sector17Code"],
            sector_17_code_name=response["Sector17CodeName"],
            sector_33_code=response["Sector33Code"],
            sector_33_code_name=response["Sector33CodeName"],
            scale_category=response["ScaleCategory"],
            market_code=response["MarketCode"],
            market_code_name=response["MarketCodeName"],
            margin_code=response.get("MarginCode"),
            margin_code_name=response.get("MarginCodeName"),
        )
    
    @staticmethod
    def to_dtos(responses: List[JQuantsListedInfoResponse]) -> List[ListedInfoDTO]:
        """Convert list of J-Quants responses to ListedInfoDTOs.
        
        Args:
            responses: List of J-Quants listed info responses
            
        Returns:
            List of ListedInfoDTO instances
        """
        return [JQuantsListedInfoMapper.to_dto(response) for response in responses]
    
    @staticmethod
    def validate_response(response: dict) -> bool:
        """Validate J-Quants response structure.
        
        Args:
            response: Response dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = [
            "Date", "Code", "CompanyName",
            "Sector17Code", "Sector17CodeName",
            "Sector33Code", "Sector33CodeName",
            "ScaleCategory", "MarketCode", "MarketCodeName"
        ]
        
        return all(field in response for field in required_fields)