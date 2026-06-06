"""Configuration management for TUIDash."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def get_config_paths() -> list[Path]:
    """Get list of paths to search for .env file."""
    paths = []
    
    # For PyInstaller bundled app - look next to executable
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).parent
        paths.append(exe_dir / ".env")
        paths.append(exe_dir / "tuidash.env")
    
    # Current working directory
    paths.append(Path.cwd() / ".env")
    
    # Project root (development) - only add if __file__ is available
    try:
        project_root = Path(__file__).parent.parent / ".env"
        paths.append(project_root)
    except (NameError, AttributeError):
        # __file__ may not be available in some PyInstaller configurations
        pass
    
    # User home directory
    paths.append(Path.home() / ".tuidash.env")
    paths.append(Path.home() / ".config" / "tuidash" / ".env")
    
    return paths


def get_config_save_path() -> Path:
    """Get the path to save config (prefers location next to exe or home dir)."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent / ".env"
    return Path.home() / ".tuidash.env"


# Load .env from first available location
for env_path in get_config_paths():
    if env_path.exists():
        load_dotenv(env_path)
        break


class Config:
    """Application configuration loaded from environment variables."""

    # Location settings (Seattle downtown)
    LATITUDE: float = float(os.getenv("LATITUDE", "47.6062"))
    LONGITUDE: float = float(os.getenv("LONGITUDE", "-122.3321"))

    # NOAA Tides station ID (Seattle)
    TIDES_STATION_ID: str = os.getenv("TIDES_STATION_ID", "9447130")

    # WSDOT Ferries API
    WSDOT_API_KEY: str = os.getenv("WSDOT_API_KEY", "")

    # Refresh interval in seconds (5 minutes)
    REFRESH_INTERVAL: int = int(os.getenv("REFRESH_INTERVAL", "300"))

    # Ferry route (Edmonds-Kingston)
    FERRY_ROUTE: str = os.getenv("FERRY_ROUTE", "ed-king")

    @classmethod
    def set_api_key(cls, key: str) -> None:
        """Set the WSDOT API key and save to config file."""
        cls.WSDOT_API_KEY = key
        os.environ["WSDOT_API_KEY"] = key
        
        # Save to config file
        config_path = get_config_save_path()
        
        # Read existing config or start fresh
        existing_lines = []
        if config_path.exists():
            try:
                existing_lines = config_path.read_text().splitlines()
            except (IOError, OSError):
                # If we can't read, just continue with empty lines
                existing_lines = []
        
        # Update or add the API key line
        key_found = False
        for i, line in enumerate(existing_lines):
            if line.startswith("WSDOT_API_KEY="):
                existing_lines[i] = f"WSDOT_API_KEY={key}"
                key_found = True
                break
        
        if not key_found:
            existing_lines.append(f"WSDOT_API_KEY={key}")
        
        # Write back - with error handling
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text("\n".join(existing_lines) + "\n")
        except (IOError, OSError, PermissionError) as e:
            # Silently fail if we can't write - app will still work with in-memory config
            print(f"Warning: Could not save API key to {config_path}: {e}", file=sys.stderr)

    @classmethod
    def validate(cls) -> list[str]:
        """Validate configuration and return list of missing required values."""
        missing = []
        if not cls.WSDOT_API_KEY:
            missing.append("WSDOT_API_KEY")
        return missing
