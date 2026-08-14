from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.vrchat_manifest import MANIFEST_SCHEMA_VERSION, BoardGameModuleManifest, ModuleBinding

CATALOG_SCHEMA_VERSION = "1.0"


class CatalogModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class PublicationStatus(StrEnum):
    PLAYABLE = "playable"
    UNAVAILABLE = "unavailable"
    UNSUPPORTED = "unsupported"
    RETIRED = "retired"
    INVALID = "invalid"


class ManifestReadStatus(StrEnum):
    AVAILABLE = "available"
    NOT_REGISTERED = "not_registered"
    UNAVAILABLE = "unavailable"
    UNSUPPORTED = "unsupported"
    RETIRED = "retired"
    INVALID = "invalid"


class BindingRegistryEntry(CatalogModel):
    slug: str = Field(min_length=1)
    ruleset_id: str = Field(alias="rulesetId", min_length=1)
    binding: ModuleBinding
    publication_status: PublicationStatus = Field(alias="publicationStatus")
    reason_code: str | None = Field(default=None, alias="reasonCode")
    snapshot_at: datetime = Field(alias="snapshotAt")

    @model_validator(mode="after")
    def validate_snapshot(self):
        if self.snapshot_at.tzinfo is None or self.snapshot_at.utcoffset() is None:
            raise ValueError("snapshotAt must include a timezone offset")
        if self.publication_status != PublicationStatus.PLAYABLE and not self.reason_code:
            raise ValueError("non-playable binding requires reasonCode")
        return self


class BindingRegistryFile(CatalogModel):
    schema_version: Literal["1.0"] = Field(default=CATALOG_SCHEMA_VERSION, alias="schemaVersion")
    entries: list[BindingRegistryEntry] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_entries(self):
        keys = [(entry.slug, entry.ruleset_id) for entry in self.entries]
        if len(keys) != len(set(keys)):
            raise ValueError("binding registry entries must have unique slug/rulesetId pairs")
        return self


class ManifestCatalogEntry(CatalogModel):
    slug: str
    ruleset_id: str = Field(alias="rulesetId")
    module_id: str = Field(alias="moduleId")
    module_version_range: str = Field(alias="moduleVersionRange")
    status: PublicationStatus
    reason_code: str | None = Field(default=None, alias="reasonCode")
    manifest_path: str = Field(alias="manifestPath")
    manifest_schema_version: Literal["1.0"] = Field(
        default=MANIFEST_SCHEMA_VERSION,
        alias="manifestSchemaVersion",
    )


class ManifestCatalog(CatalogModel):
    schema_version: Literal["1.0"] = Field(default=CATALOG_SCHEMA_VERSION, alias="schemaVersion")
    catalog_revision: str = Field(alias="catalogRevision", min_length=64, max_length=64)
    manifest_schema_version: Literal["1.0"] = Field(
        default=MANIFEST_SCHEMA_VERSION,
        alias="manifestSchemaVersion",
    )
    entries: list[ManifestCatalogEntry] = Field(default_factory=list)


class ManifestReadResponse(CatalogModel):
    schema_version: Literal["1.0"] = Field(default=CATALOG_SCHEMA_VERSION, alias="schemaVersion")
    status: ManifestReadStatus
    slug: str
    ruleset_id: str = Field(alias="rulesetId")
    reason_code: str | None = Field(default=None, alias="reasonCode")
    manifest: BoardGameModuleManifest | None = None
