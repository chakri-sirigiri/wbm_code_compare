import hashlib
from pathlib import Path

from src.models.base import AssetBase
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class FlowService(AssetBase):
    """Represents an IS Flow Service."""

    package_name: str
    asset_type: str = "flow_service"


class Package(AssetBase):
    """Represents an IS Package."""

    asset_type: str = "package"
    services: list[FlowService] = []


class Properties(AssetBase):
    """Represents an IS Property file."""

    asset_type: str = "properties"
    env_prefix: str | None = None


def calculate_sha256(path: Path) -> str:
    """Calculate SHA256 of a file or directory content."""
    sha256_hash = hashlib.sha256()
    if path.is_file():
        with open(path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
    elif path.is_dir():
        # For directories (like services), we hash all relevant files
        for file in sorted(path.rglob("*")):
            if file.is_file() and not file.name.startswith("."):
                sha256_hash.update(file.name.encode())
                with open(file, "rb") as f:
                    for byte_block in iter(lambda: f.read(4096), b""):
                        sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def discover_packages(root_path: Path) -> list[Package]:
    """Discover IS Packages and their services."""
    discovered = []

    # Check if root_path itself is a Packages dir or contains assets/IS/Packages
    packages_dir = root_path
    if (root_path / "assets" / "IS" / "Packages").exists():
        packages_dir = root_path / "assets" / "IS" / "Packages"

    if not packages_dir.exists() or not packages_dir.is_dir():
        return discovered

    for pkg_dir in sorted(packages_dir.iterdir()):
        if pkg_dir.is_dir() and (pkg_dir / "manifest.v3").exists():
            pkg = Package(
                name=pkg_dir.name,
                f_path=str(pkg_dir),
                sha256=calculate_sha256(pkg_dir),
                services=[],
            )

            # Discover services
            services_root = pkg_dir / "ns"
            if services_root.exists():
                for svc_file in services_root.rglob("flow.xml"):
                    svc_dir = svc_file.parent
                    parts = svc_dir.relative_to(services_root).parts
                    if len(parts) > 1:
                        svc_name = f"{'.'.join(parts[:-1])}:{parts[-1]}"
                    else:
                        svc_name = parts[0]
                    svc = FlowService(
                        name=svc_name,
                        package_name=pkg.name,
                        f_path=str(svc_dir),
                        sha256=calculate_sha256(svc_dir),
                    )
                    pkg.services.append(svc)

            discovered.append(pkg)

    logger.info(f"Discovered {len(discovered)} packages")
    return discovered


def discover_properties(root_path: Path) -> list[Properties]:
    """Discover IS Property files."""
    discovered = []

    properties_dir = root_path
    if (root_path / "assets" / "IS" / "Properties").exists():
        properties_dir = root_path / "assets" / "IS" / "Properties"

    if not properties_dir.exists() or not properties_dir.is_dir():
        return discovered

    prefixes = ["DV_", "IT_", "UA_", "PD_"]
    for f in sorted(properties_dir.iterdir()):
        if f.is_file() and any(f.name.startswith(p) for p in prefixes):
            env = f.name.split("_")[0]
            discovered.append(
                Properties(name=f.name, f_path=str(f), sha256=calculate_sha256(f), env_prefix=env)
            )

    logger.info(f"Discovered {len(discovered)} properties")
    return discovered


def discover_all_assets(root_path: Path) -> list[AssetBase]:
    """Discover all webMethods assets (Packages + Properties)."""
    assets = []
    assets.extend(discover_packages(root_path))
    assets.extend(discover_properties(root_path))
    return assets


def flatten_assets(assets: list[AssetBase]) -> list[AssetBase]:
    """Flatten hierarchical asset list."""
    flat = []
    for asset in assets:
        flat.append(asset)
        if isinstance(asset, Package):
            flat.extend(asset.services)
    return flat
