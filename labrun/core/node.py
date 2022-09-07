import yaml
from jinja2 import Environment, FileSystemLoader
from pkg_resources import resource_filename
from pygnmi.client import gNMIException

from .gnmirunner import GnmiRunner
from .util import log_config

# create logger
logger = log_config(__name__)


class Node:
    """Class defines oblects and methods related to network device"""

    def __init__(
        self,
        node_name,
        node_dict,
        config_template,
        lab_name,
        topology,
        loopback_prefix,
        p2p_prefix,
        virtual_env,
    ):
        self.node_name = node_name
        self.lab_name = lab_name
        self.config_template = config_template
        self.node_dict = node_dict
        self.config_template_flag = self.node_dict["config_template"]
        self.loopback_prefix = loopback_prefix
        self.p2p_prefix = p2p_prefix
        self.virtual_env = virtual_env
        self.vendor = self.node_dict["vendor"]
        self.model = self.node_dict["model"]
        self.sw = "21.10.R1"
        self.license_path = "lic.txt"
        self.username = "admin"
        self.password = "admin"
        self.gnmi_port = "57400"
        self.target_configuration = self.node_dict["configuration"]
        self.node_links_dict = topology.collect_links(self.node_name)
        self._target_xpath = []
        self._bootstrap_xpath = []
        self._node_config_params = {"name": self.node_name}
        self._model_jinja_tmpl_path = resource_filename(
            "labrun", f"templates/vendors/{self.vendor}"
        )
        self._model_jinja_tmpl = f"{self.model}_bootstrap.tmpl"
        self._model_params_filename = (
            f"{self._model_jinja_tmpl_path}/{self.model}_bootstrap.yaml"
        )
        self._bootstrap_interfaces_data = {"interfaces": {}, "loopback": {}}
        self.address = f"{self.virtual_env}-{self.lab_name}-{self.node_name}"
        self._gnmi_instance = None
        self.bootstrap_completed = None
        self.gnmi_errors = []

    @staticmethod
    def _read_yaml(filename):
        with open(filename) as f:
            data = yaml.safe_load(f)
        return data

    @staticmethod
    def _render_jinja(templ_path, templ_name, data_dict):
        env = Environment(loader=FileSystemLoader(templ_path))
        templ = env.get_template(templ_name)
        raw_config = templ.render(data_dict)
        return raw_config

    def _xpath_gen(self, input_dict, path=None):
        if not path:
            path = []
        if isinstance(input_dict, dict):
            for key in input_dict.keys():
                local_path = path[:]
                local_path.append(key)
                for xpath_and_value in self._xpath_gen(input_dict[key], local_path):
                    yield xpath_and_value
        else:
            yield path, input_dict

    def _build_target_xpath(self, input_dict):
        xpath_list = [
            ("/" + "/".join(xpath), value)
            for xpath, value in self._xpath_gen(input_dict)
        ]
        return xpath_list

    @property
    def target_xpath(self):
        if not self._target_xpath:
            if self.config_template_flag:
                self._target_xpath.extend(
                    self._build_target_xpath(self.config_template)
                )
            self._target_xpath.extend(
                self._build_target_xpath(self.target_configuration)
            )
        return self._target_xpath

    @property
    def bootstrap_interfaces_data(self):
        if not self._bootstrap_xpath:
            for local_side, remote_side in self.node_links_dict.items():
                if not self.p2p_prefix.find_p2p_address(local_side, remote_side):
                    address = self.p2p_prefix.allocate_p2p_network(
                        local_side, remote_side
                    )
                else:
                    address = self.p2p_prefix.find_p2p_address(local_side, remote_side)
                int_name = f"to_{remote_side.split('-')[0]}"
                port = local_side.split("-")[1][-1]
                self._bootstrap_interfaces_data["interfaces"].update(
                    {
                        int_name: {
                            "address": address,
                            "prefix_length": 31,
                            "port": port,
                        }
                    }
                )
            self._bootstrap_interfaces_data["loopback"].update(
                {"address": self.loopback_prefix.allocate_next_free_ip(loopback=True)}
            )
        return self._bootstrap_interfaces_data

    @property
    def node_config_params(self):
        # read model related data
        self._node_config_params.update(self._read_yaml(self._model_params_filename))
        # add interface data
        self._node_config_params.update(self.bootstrap_interfaces_data)
        return self._node_config_params

    @property
    def bootstrap_xpath(self):
        if not self._bootstrap_xpath:
            raw_config = self._render_jinja(
                self._model_jinja_tmpl_path,
                self._model_jinja_tmpl,
                self.node_config_params,
            )
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

    def bootstrap_precheck(self):
        precheck_flags = []
        precheck_flags.append(self._gnmi_probe())
        return True if all(precheck_flags) else False

    def bootstrap_postcheck(self):
        postcheck_flags = []
        if not self.gnmi_errors:
            postcheck_flags.append(True)
        return True if all(postcheck_flags) else False

    def set_config_blocks(self, config_blocks, bootstrap=False):
        with self.gnmi_instance as conn:
            logger.info(f"{self.node_name} gNMI connection is running")
            for block in config_blocks:
                logger.debug(f"\nSet block on {self.node_name}\n{block}\n")
                try:
                    rpc_reply = conn.set(update=block)
                except gNMIException as error:
                    logger.debug(
                        f"Setting block on {self.node_name} is failed with error:\n {error}"
                    )
                    logger.warning(
                        f"Setting block on {self.node_name} is failed. Check logs for details"
                    )
                    self.gnmi_errors.append(error)
                logger.debug(f"{self.node_name} reply\n{rpc_reply}\n")
        logger.info(f"{self.node_name} gNMI connection is closed")
        if bootstrap:
            if self.bootstrap_postcheck():
                self.bootstrap_completed = True
            else:
                self.bootstrap_completed = False
                logger.info(f"{self.node_name} bootstrap is failed")
        return self.node_name

