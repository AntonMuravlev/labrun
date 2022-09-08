from typing import TypedDict

from pydantic import BaseModel, validator

from .network import IPv4Network
from .topology import Topology

VIRTUAL_ENVS = ("clab",)
SUPPORTED_PLATFORMS = {
    "nokia": ("sr-1",),
}

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
    loopback_prefix: IPv4Network
    p2p_prefix: IPv4Network
    config_template: dict
    nodes: dict[str, NodeData]
    topology: Topology

    @validator("virtual_env")
    def validate_virtual_env_type(cls, value):
        if value not in VIRTUAL_ENVS:
            raise ValueError(
                f"{value} is not supported as a virtual_env\n"
                f"Labrun only supports the next types of envs: {','.join(VIRTUAL_ENVS)}"
            )
        return value

    @validator("nodes")
    def validate_vendor_and_model(cls, value):
        for node in value.keys():
            current_vendor = value[node]["vendor"]
            current_model = value[node]["model"]
            vendors = tuple(SUPPORTED_PLATFORMS.keys())
            models = SUPPORTED_PLATFORMS[current_vendor]
            if current_vendor not in vendors:
                raise ValueError(
                    f"{current_vendor} is not supported\n"
                    f"Labrun only supports the next types of vendors: {','.join(vendors)}"
                )
            if current_model not in models:
                raise ValueError(
                    f"{current_model} is not supported\n"
                    f"Labrun only supports the next types of {current_vendor}"
                    f" models: {','.join(models)}"
                )
        return value
