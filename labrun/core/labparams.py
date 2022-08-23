from pydantic import BaseModel

from .network import IPv4Network
from .topology import Topology


class LabParams(BaseModel):
    """Pydantic based class. It parses and validate input data.
    GlobalParams.parse_obj(input_dict) returns defined instances"""

    lab_name: str
    loopback_prefix: IPv4Network
    p2p_prefix: IPv4Network
    nodes: dict
    topology: Topology
