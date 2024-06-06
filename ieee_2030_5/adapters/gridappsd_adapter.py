from attrs import define, field
from gridappsd import GridAPPSD
from ieee_2030_5.certs import TLSRepository


@define
class GridAPPSDAdapter:
    gapps: GridAPPSD
    model_name: str
    model_id: str = field(default=None)

    def create_der_client_certificates(self, tls: TLSRepository):
        models = self.gapps.query_model_info()
        for m in models['data']['models']:
            if m['modelName'] == self.model_name:
                self.model_id = m['modelId']
                break
        if not self.model_id:
            raise ValueError(f"Model {self.model_name} not found")

        from cimgraph.data_profile import CIM_PROFILE
        import cimgraph.data_profile.rc4_2021 as cim
        from cimgraph.models import FeederModel
        from cimgraph.databases.gridappsd import GridappsdConnection
        from cimgraph.databases import ConnectionParameters

        cim_profile = CIM_PROFILE.RC4_2021.value
        iec = 7
        params = ConnectionParameters(cim_profile=cim_profile, iec61970_301=iec)

        conn = GridappsdConnection(params)
        conn.cim_profile = cim_profile
        feeder = cim.Feeder(mRID=self.model_id)

        network = FeederModel(connection=conn, container=feeder, distributed=False)

        network.get_all_edges(cim.PowerElectronicsConnection)

        for inv in network.graph[cim.PowerElectronicsConnection].values():
            tls.create_cert(inv.mRID)
