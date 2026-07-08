import os
from typing import Optional


class TenantStorage:
    """
    Resolves data paths partition for files under the tenants context directory.
    """
    @staticmethod
    def get_tenant_path(base_path: str, tenant_id: Optional[str]) -> str:
        if not tenant_id:
            return base_path

        # Standardise and strip leading parts
        cleaned_path = base_path.lstrip("./").lstrip("/")
        if cleaned_path.startswith("data/"):
            cleaned_path = cleaned_path[len("data/"):]
        elif cleaned_path.startswith("data\\"):
            cleaned_path = cleaned_path[len("data\\"):]

        return os.path.normpath(os.path.join("data", "tenants", tenant_id, cleaned_path))
