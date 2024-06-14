ENABLED = True
try:
    from attrs import define, field
    from gridappsd import GridAPPSD
    from cimgraph.data_profile import CIM_PROFILE
    import cimgraph.data_profile.rc4_2021 as cim
    from cimgraph.models import FeederModel
    from cimgraph.databases.gridappsd import GridappsdConnection
    from cimgraph.databases import ConnectionParameters
except ImportError:
    ENABLED = False
from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.config import DeviceConfiguration


if ENABLED:
    @define
    class GridAPPSDAdapter:
        gapps: GridAPPSD
        model_name: str
        default_pin: str
        model_id: str = field(default=None)
        devices: list[DeviceConfiguration] = []
        power_electronic_connections: list[cim.PowerElectronicsConnection] = []

        def _load_power_electronic_connections(self):
            models = self.gapps.query_model_info()
            for m in models['data']['models']:
                if m['modelName'] == self.model_name:
                    self.model_id = m['modelId']
                    break
            if not self.model_id:
                raise ValueError(f"Model {self.model_name} not found")

            cim_profile = CIM_PROFILE.RC4_2021.value
            iec = 7
            params = ConnectionParameters(cim_profile=cim_profile, iec61970_301=iec)

            conn = GridappsdConnection(params)
            conn.cim_profile = cim_profile
            feeder = cim.Feeder(mRID=self.model_id)

            network = FeederModel(connection=conn, container=feeder, distributed=False)

            network.get_all_edges(cim.PowerElectronicsConnection)
            self.power_electronic_connections = network.graph[cim.PowerElectronicsConnection].values()

        def __attrs_post_init__(self):
            self._load_power_electronic_connections()

        def _build_device_configurations(self):
            self.devices = []
            for inv in self.power_electronic_connections:
                dev = DeviceConfiguration(
                    id=inv.mRID,
                    pin=self.default_pin
                )
                self.devices.append(dev)

        def get_device_configurations(self) -> list[DeviceConfiguration]:
            if not self.devices:
                self._build_device_configurations()
            return self.devices

        def create_2030_5_device_certificates_and_configurations(self, tls: TLSRepository) -> list[DeviceConfiguration]:

            self.devices = []
            for inv in self.power_electronic_connections:
                tls.create_cert(inv.mRID)
            self._build_device_configurations()
            return self.devices
