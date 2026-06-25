from pydantic import BaseModel
from typing import Optional


class QuestionRequest(BaseModel):
    question: str
    agreement: Optional[str] = None


class AgreementOption(BaseModel):
    pdf_name: str
    display_name: str
    agreement_date: str
    parties: list[str]


class QuestionResponse(BaseModel):
    answer: str = ""
    requires_selection: bool = False
    agreements: list[AgreementOption] = []
    source_pdf: Optional[str] = None
    source_page: Optional[int] = None
    cited_pages: list[int] = []
    confidence: int = 0