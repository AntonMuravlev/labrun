import yaml

from jinja2 import Environment, FileSystemLoader
from concurrent.futures import ThreadPoolExecutor, as_completed

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
                        self.labparams.config_template,
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
                    logger.info(f"{node.node_name} bootstrap precheck is successful")
                    future = executor.submit(
                        node.set_config_blocks, node.bootstrap_xpath, bootstrap=True
                    )
                else:
                    logger.warning(f"{node.node_name} failed bootstrap_precheck!")

    def push_config_to_nodes(self, nobootstrap=False):
        futures = []
        with ThreadPoolExecutor(max_workers=len(self.node_instances)) as executor:
            for node in self.node_instances:
                if node.bootstrap_completed or nobootstrap:
                    logger.info(f"{node.node_name} configuration is starting")
                    future = executor.submit(
                        node.set_config_blocks,
                        [node.target_xpath],  # push config as a one block
                    )
                    futures.append(future)
                else:
                    logger.warning(f"{node.node_name} is not ready to configure")
            for _ in as_completed(futures):
                try:
                    result = _.result()
                except Exception as error:
                    logger.debug(f"Future returns exception. Exception - {error}")

    def config_post_check(self):
        for node in self.node_instances:
            if not node.gnmi_errors:
                logger.info(
                    f"{node.node_name} configuration is completed without gnmi errors"
                )
            else:
                logger.info(
                    f"{node.node_name} configuration is failed. Please check log files"
                )
