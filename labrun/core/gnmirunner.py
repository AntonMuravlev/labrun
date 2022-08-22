from pygnmi.client import gNMIclient, gNMIException


class GnmiRunner(gNMIclient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
