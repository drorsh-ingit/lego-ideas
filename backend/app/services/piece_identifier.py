from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import httpx

from app.core.config import settings


@dataclass
class IdentifiedPiece:
    part_num: str
    confidence: float
    color_id: int | None = None


@dataclass
class IdentificationResult:
    pieces: list[IdentifiedPiece]
    raw_response: dict


class PieceIdentifier(ABC):
    @abstractmethod
    async def identify(self, image_bytes: bytes) -> IdentificationResult:
        ...


class BrickognizeIdentifier(PieceIdentifier):
    async def identify(self, image_bytes: bytes) -> IdentificationResult:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.brickognize_api_url}/predict/parts/",
                files={"query_image": ("photo.jpg", image_bytes, "image/jpeg")},
            )
            response.raise_for_status()
            data = response.json()

        pieces = [
            IdentifiedPiece(
                part_num=item["id"],
                confidence=item.get("score", 0.0),
                color_id=None,  # Brickognize does not return color
            )
            for item in data.get("items", [])
        ]
        return IdentificationResult(pieces=pieces, raw_response=data)


def get_identifier() -> PieceIdentifier:
    return BrickognizeIdentifier()
