from typing import TypedDict

from pydantic import BaseModel, validator

from .network import IPv4Network
from .topology import Topology

VIRTUAL_ENVS = ("clab",)

# check node dict keys by pydantic and TypedDict
class NodeData(TypedDict):
    config_template: bool
    vendor: str
    model: str
    configuration: dict


class LabParams(BaseModel):
    """Pydantic based class. It parses and validate input data.
    GlobalParams.parse_obj(input_dict) returns defined instances"""

    lab_name: str
    virtual_env: str
    loopback_prefix: IPv4Network  # develop validator
    p2p_prefix: IPv4Network  # develop validator
    config_template: dict
    nodes: dict[str, NodeData]
    topology: Topology  # develop validator

    @validator("virtual_env")
    def virtual_env_name(cls, v):
        if v not in VIRTUAL_ENVS:
            raise ValueError(
                f"{v} is not supported as a virtual_env\n"
                f"Labrun only supports the next types of envs: {','.join(VIRTUAL_ENVS)}"
            )
        return v.title()
