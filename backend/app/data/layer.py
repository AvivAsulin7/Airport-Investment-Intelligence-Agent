"""Wire the data sources together for the engine (Phase 6) and tools (Phase 7)."""

from dataclasses import dataclass

from app.data.airports import AirportReference
from app.data.bts_api import BtsTrafficClient
from app.data.operations import OperationsData
from app.data.routes import RouteData
from app.data.snapshots import SnapshotStore
from app.settings import Settings

FALLBACK_FILE = "bts_api_fallback.json"


@dataclass
class DataLayer:
    traffic: BtsTrafficClient  # live public API
    airports: AirportReference  # FAA snapshot
    operations: OperationsData  # BTS on-time snapshot
    routes: RouteData  # BTS T-100 snapshot
    snapshots: SnapshotStore


def load_data_layer(settings: Settings) -> DataLayer:
    store = SnapshotStore.load(settings.data_processed_dir)
    fallback = settings.data_processed_dir / FALLBACK_FILE
    return DataLayer(
        traffic=BtsTrafficClient(settings, fallback_path=fallback if fallback.is_file() else None),
        airports=AirportReference(store),
        operations=OperationsData(store),
        routes=RouteData(store),
        snapshots=store,
    )
