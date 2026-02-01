from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict

# Load .env file
load_dotenv()


class BaseAsset(BaseModel):
    """Base class for all domain objects."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        populate_by_name=True,
    )


class AssetBase(BaseAsset):
    """Base for discoverable assets (Package, Service, etc)."""

    name: str
    f_path: str
    asset_type: str
    sha256: str | None = None

    @property
    def asset_id(self) -> str:
        """Unique identifier for the asset."""
        return f"{self.asset_type}:{self.name}"
