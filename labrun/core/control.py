import yaml
import sys

from jinja2 import Environment, FileSystemLoader
from concurrent.futures import ThreadPoolExecutor, as_completed
from pydantic import ValidationError

from .labparams import LabParams
from .node import Node
from .util import log_config

# create logger
logger = log_config(__name__)


class Control:
    def __init__(self, topo_file_name):
        self.topo_file_name = topo_file_name
        self._file_data = None
        self._labparams = None
        self._node_instances = []

    @property
    def file_data(self):
        if not self._file_data:
            logger.debug("Reading input lab file")
            try:
                with open(self.topo_file_name) as f:
                    self._file_data = yaml.safe_load(f)
            except FileNotFoundError as e:
                logger.critical(f"[bold red]Input lab file not found[/bold red]")
                sys.exit(1)
        return self._file_data

    @property
    def labparams(self):
        if not self._labparams:
            try:
                self._labparams = LabParams.parse_obj(self.file_data)
            except ValidationError as e:
                logger.critical(
                    f"[bold red]Input lab file has incorrect values[/bold red]\nPydantic errors: {e}"
                )
                sys.exit(1)
        return self._labparams

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
                        self.labparams.virtual_env,
                    )
                )
            logger.debug("Creating node instances is completed")
        return self._node_instances

    def bootstrap_nodes(self):
        with ThreadPoolExecutor(max_workers=len(self.node_instances)) as executor:
            for node in self.node_instances:
                if node.bootstrap_precheck():
                    logger.info(
                        f"[green]{node.node_name} bootstrap precheck is successful[/green]"
                    )
                    future = executor.submit(
                        node.set_config_blocks, node.bootstrap_xpath, bootstrap=True
                    )
                else:
                    logger.warning(
                        f"[bold red]{node.node_name} failed bootstrap_precheck![/bold red]"
                    )

    def push_config_to_nodes(self, nobootstrap=False):
        futures = []
        with ThreadPoolExecutor(max_workers=len(self.node_instances)) as executor:
            for node in self.node_instances:
                if node.bootstrap_completed or nobootstrap:
                    logger.info(
                        f"[cyan]{node.node_name} configuration is starting[/cyan]"
                    )
                    future = executor.submit(
                        node.set_config_blocks,
                        [node.target_xpath],  # push config as a one block
                    )
                    futures.append(future)
                else:
                    logger.warning(
                        f"[bold red]{node.node_name} is not ready to configure[/bold red]"
                    )
            for _ in as_completed(futures):
                try:
                    result = _.result()
                except Exception as error:
                    logger.debug(
                        f"[bold red]Future returns exception. Exception - {error}[/bold red]"
                    )

    def config_post_check(self):
        for node in self.node_instances:
            if not node.gnmi_errors:
                logger.info(
                    f"[green]{node.node_name} configuration is completed without gnmi errors[/green]"
                )
            else:
                logger.info(
                    f"[bold red]{node.node_name} configuration is failed. Please check log files[/bold red]"
                )
