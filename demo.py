import yaml
import ipaddress
from jinja2 import Environment, FileSystemLoader
from pygnmi.client import gNMIclient
from pydantic import BaseModel
from pprint import pprint
from custom_ipv4net import MyIPv4Network
from topology import Topology


class GlobalParams(BaseModel):
    """Pydantic based class. It parses and validate input data.
    GlobalParams.parse_obj(input_dict) returns defined instances"""

    lab_name: str
    loopback_prefix: MyIPv4Network
    p2p_prefix: MyIPv4Network
    nodes: dict
    topology: Topology


class Node:
    """Class defines oblects and methods related to network device"""

    def __init__(
        self,
        node_name,
        node_dict,
        lab_name,
        topology,
        loopback_prefix,
        p2p_prefix,
        virtual_env="clab",
        vendor="nokia",
        model="sr-1",
        sw="21.10.R1",
        license_path="lic.txt",
        username="admin",
        password="admin",
        gnmi_port="57400",
    ):
        self.node_name = node_name
        self.lab_name = lab_name
        self.node_dict = node_dict
        self.loopback_prefix = loopback_prefix
        self.p2p_prefix = p2p_prefix
        self.virtual_env = virtual_env
        self.vendor = vendor
        self.model = model
        self.sw = sw
        self.license_path = license_path
        self.username = username
        self.password = password
        self.gnmi_port = gnmi_port
        self.target_configuration = self.node_dict["configuration"]
        self.node_links_dict = topology.collect_links(self.node_name)
        self._target_xpath = []
        self._bootstrap_xpath = []
        self._model_data = {"name": self.node_name}
        self._bootstrap_interfaces_data = {"interfaces": {}, "loopback": {}}
        self.address = f"{self.virtual_env}-{self.lab_name}-{self.node_name}"
        self._gnmi_instance = None

    def _xpath_gen(self, input_dict, path=None):
        if not path:
            path = []
        if isinstance(input_dict, dict):
            for key in input_dict.keys():
                local_path = path[:]
                local_path.append(key)
                for b in self._xpath_gen(input_dict[key], local_path):
                    yield b
        else:
            yield path, input_dict

    @property
    def target_xpath(self):
        self._target_xpath = [
            ("/" + "/".join(x[0]), x[1])
            for x in self._xpath_gen(self.target_configuration)
        ]
        return self._target_xpath

    @property
    def bootstrap_interfaces_data(self):
        for local_side, remote_side in self.node_links_dict.items():
            if not self.p2p_prefix.find_p2p_address(local_side, remote_side):
                address = self.p2p_prefix.allocate_p2p_network(local_side, remote_side)
            else:
                address = self.p2p_prefix.find_p2p_address(local_side, remote_side)
            int_name = f"to_{remote_side.split('-')[0]}"
            port = local_side.split("-")[1][-1]
            self._bootstrap_interfaces_data["interfaces"].update(
                {
                    int_name: {
                        "p2p_address": address,
                        "prefix_length": 31,
                        "port": port,
                    }
                }
            )
        self._bootstrap_interfaces_data["loopback"].update(
            {"address": self.loopback_prefix.allocate_next_free_ip()}
        )
        return self._bootstrap_interfaces_data

    @staticmethod
    def _read_yaml(filename):
        with open(filename) as f:
            data = yaml.safe_load(f)
        return data

    @staticmethod
    def _render_jinja(templ_path, templ_name, data_dict):
        env = Environment(loader=FileSystemLoader(templ_path))  # need to fix templ path
        templ = env.get_template(templ_name)
        raw_config = templ.render(data_dict)
        return raw_config

    @property
    def bootstrap_xpath(self):
        self._model_data.update(
            self._read_yaml(
                f"templates/vendors/{self.vendor}/{self.model}_bootstrap.yaml"
            )
        )#read model related data
        self._model_data.update(self.bootstrap_interfaces_data)  # add interface data
        raw_config = self._render_jinja(".", "bootstrap.tmpl", self._model_data)
        # terrible list comp!
        self._bootstrap_xpath = [
            [
                tuple((int(l) if l.isdigit() else l for l in line.split(",")))
                for line in block.split("\n")
                if line
            ]
            for block in raw_config.strip().split("**logic_block**")
            if block
        ]
        return self._bootstrap_xpath

    @property
    def gnmi_instance(self):
        if not self._gnmi_instance:
            self._gnmi_instance = GnmiRunner(
                target=(self.address, self.gnmi_port),
                username=self.username,
                password=self.username,
                insecure=True,
            )
        return self._gnmi_instance

    # add try/except
    def _gnmi_probe(self):
        with self.gnmi_instance as connection:
            capabilities = connection.capabilities()
        return True if capabilities else False

    @property
    def current_config(self):
        pass


class GnmiRunner(gNMIclient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ControlCenter:
    def __init__(self, topo_file_name):
        self.topo_file_name = topo_file_name
        self._file_data = None
        self.global_params = GlobalParams.parse_obj(self.file_data)
        self._node_instances = []

    @property
    def file_data(self):
        with open(self.topo_file_name) as f:
            self._file_data = yaml.safe_load(f)
        return self._file_data

    @property
    def node_instances(self):
        if not self._node_instances:
            self._node_instances = [
                Node(
                    node_name,
                    self.global_params.nodes[node_name],
                    self.global_params.lab_name,
                    self.global_params.topology,
                    self.global_params.loopback_prefix,
                    self.global_params.p2p_prefix,
                )
                for node_name in self.global_params.nodes.keys()
            ]
        return self._node_instances

    def bootstrap_precheck(self, node):
        print(f"{node.node_name} bootstrap_precheck is on going")
        precheck_flags = []
        precheck_flags.append(node._gnmi_probe())
        return True if all(precheck_flags) else False

    def bootstrap_nodes(self):
        for node in self.node_instances:
            if self.bootstrap_precheck(node):
                print(f"{node.node_name} bootstrap_prechecki is successful")
                with node.gnmi_instance as conn:
                    print(f"Starting {node.node_name} bootstrap")
                    for block in node.bootstrap_xpath:
                        print(f"\nSet block\n{block}\n")
                        rpc_reply = conn.set(update=block)
                        print(f"Node_reply\n{rpc_reply}\n")
                    if self.bootstrap_postcheck(node):
                        print(f"{node.node_name} bootstrap_postcheck is successful")
                        print(f"{node.node_name} bootstrap is completed")
                    else:
                        print(f"{node.node_name} failed bootstrap_postcheck!")
                        print(f"{node.node_name} bootstrap failed")
            else:
                print(f"{node.node_name} failed bootstrap_precheck!")

    def bootstrap_postcheck(self, node):
        print(f"{node.node_name} bootstrap_postcheck is on going")
        return True

    def push_config_to_nodes(self):
        pass

    def config_post_check(self):
        pass


if __name__ == "__main__":
   cc = ControlCenter("ospf_bgp_topo.yml")
   cc.global_params.loopback_prefix.allocate_next_free_ip()
   cc.bootstrap_nodes()
##    P1 = cc.node_instances[0]
#    P2 = cc.node_instances[1]
#    P3 = cc.node_instances[2]
#    P4 = cc.node_instances[3]
##    P1_gc = GnmiRunner(
##        target=(P1.address, P1.gnmi_port),
##        username="admin",
##        password="admin",
##        insecure=True,
##    )
##    P2_gc = GnmiRunner(
##        target=(P2.address, P2.gnmi_port),
##        username="admin",
##        password="admin",
##        insecure=True,
##    )
##    P3_gc = GnmiRunner(
##        target=(P3.address, P3.gnmi_port),
##        username="admin",
##        password="admin",
##        insecure=True,
##    )
##    P4_gc = GnmiRunner(
##        target=(P4.address, P4.gnmi_port),
##        username="admin",
##        password="admin",
##        insecure=True,
##    )
##    for block in P1.bootstrap_xpath:
##        P1_gc.set(update=block)
##    for block in P2.bootstrap_xpath:
##        P2_gc.set(update=block)
##    for block in P3.bootstrap_xpath:
##        P3_gc.set(update=block)
##    for block in P4.bootstrap_xpath:
##        P4_gc.set(update=block)
##    P1_gc.set(update=P1.target_xpath)
##    P2_gc.set(update=P2.target_xpath)
##    P3_gc.set(update=P3.target_xpath)
##    P4_gc.set(update=P4.target_xpath)
##    with open("lab_topo_example.yml") as f:
#        data = yaml.safe_load(f)
#    first_lab = GlobalParams.parse_obj(data)
#    P1_data = first_lab.nodes["P1"]
#    P1 = Node("P1", P1_data, first_lab.topology)
#    P1_gc = GnmiRunner(
#        target=(P1.address, 57400), username="admin", password="admin", insecure=True
#    )
#    pprint(P1_gc.get(path=["/configure/port[port-id=1/1/c4]/description"]))
#    pprint(P1_gc.set(replace=P1.xpath_list))
