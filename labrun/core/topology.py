import sys
import re
from collections.abc import MutableMapping


class Topology(MutableMapping):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, input_topo):
        if not isinstance(input_topo, dict):
            raise TypeError("Topology should be a dict")
        # validate link form
        all_links = list(input_topo.keys()) + list((input_topo.values()))
        for link in all_links:
            if not re.match(r"\S+-eth\d+", link):
                raise ValueError(
                    f"Topology link {link} has incorrect form. Correct example - 'P1-eth1'"
                )
        return cls(input_topo)

    def __init__(self, topology_dict):
        self.topology = self._normalize(topology_dict)

    @staticmethod
    def _normalize(topology_dict):
        normalized_topology = {}
        for box, neighbor in topology_dict.items():
            if not neighbor in normalized_topology:
                if box < neighbor:
                    normalized_topology[box] = neighbor
                else:
                    normalized_topology[neighbor] = box
        return normalized_topology

    def __getitem__(self, item):
        if self.topology.get(item):
            return self.topology[item]
        elif item in self.topology.values():
            for k, v in self.topology.items():
                if v == item:
                    return k
        else:
            raise KeyError

    def __setitem__(self, key, value):
        if key in self.topology.values():
            our_key = ()
            for k, v in self.topology.items():
                if v == key:
                    our_key = k
            del self.topology[our_key]
            self.topology[value] = key
        else:
            self.topology[key] = value

    def __delitem__(self, key):
        if key in self.topology.values():
            our_key = ()
            for k, v in self.topology.items():
                if v == key:
                    our_key = k
            del self.topology[our_key]
        elif self.topology.get(key):
            del self.topology[key]
        else:
            raise KeyError

    def __iter__(self):
        return iter(self.topology)

    def __len__(self):
        return len(self.topology)

    def collect_links(self, node_name):
        all_links = list(self.topology.keys()) + list(self.topology.values())
        node_links = [link for link in all_links if node_name in link]
        node_links_dict = {local_link: self[local_link] for local_link in node_links}
        return node_links_dict
