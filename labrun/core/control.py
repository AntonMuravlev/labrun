import yaml

from jinja2 import Environment, FileSystemLoader
from pygnmi.client import gNMIException
from concurrent.futures import ThreadPoolExecutor, as_completed, wait

from .labparams import LabParams
from .node import Node
from .util import log_config

# create logger
logger = log_config(__name__)


class Control:
    def __init__(self, topo_file_name):
        self.topo_file_name = topo_file_name
        self._file_data = None
        self.labparams = LabParams.parse_obj(self.file_data)
        self._node_instances = []

    @property
    def file_data(self):
        if not self._file_data:
            logger.debug("Reading input lab file")
            with open(self.topo_file_name) as f:
                self._file_data = yaml.safe_load(f)
        return self._file_data

    @property
    def node_instances(self):
        if not self._node_instances:
            logger.debug("Creating node instances")
            for node_name in self.labparams.nodes.keys():
                self._node_instances.append(
                    Node(
                        node_name,
                        self.labparams.nodes[node_name],
                        self.labparams.lab_name,
                        self.labparams.topology,
                        self.labparams.loopback_prefix,
                        self.labparams.p2p_prefix,
                    )
                )
            logger.debug("Creating node instances is completed")
        return self._node_instances

    def bootstrap_nodes(self):
        with ThreadPoolExecutor(max_workers=len(self.node_instances)) as executor:
            for node in self.node_instances:
                if node.bootstrap_precheck():
                    logger.info(f"{node.node_name} bootstrap_precheck is successful")
                    logger.info(f"Starting {node.node_name} bootstrap")
                    future = executor.submit(
                        node.set_config_blocks, node.bootstrap_xpath, bootstrap=True
                    )
                else:
                    logger.warning(f"{node.node_name} failed bootstrap_precheck!")

    def push_config_to_nodes(self):
        with ThreadPoolExecutor(max_workers=len(self.node_instances)) as executor:
            for node in self.node_instances:
                if node.bootstrap_completed:
                    logger.info(f"Starting {node.node_name} configuration")
                    future = executor.submit(
                        node.set_config_blocks, node.target_xpath
                    )
                else:
                    logger.warning(f"{node.node_name} is not ready to configure")

    def config_post_check(self, node):
        return True


if __name__ == "__main__":
    cc = Control("../../examples/ospf_bgp_topo.yml")
    cc.labparams.loopback_prefix.allocate_next_free_ip()
    cc.bootstrap_nodes()
#    cc.push_config_to_nodes()
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
