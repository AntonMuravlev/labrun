from collections.abc import MutableMapping


class Topology(MutableMapping):
    @classmethod
    def __get_validators__(cls):
        # one or more validators may be yielded which will be called in the
        # order to validate the input, each validator will receive as an input
        # the value returned from the previous validator
        yield cls.validate

    @classmethod
    def validate(cls, value):
        if not isinstance(value, dict):
            raise TypeError("Topology should be a dict")
        return cls(value)

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
        node_links_dict = {
            local_link: self[local_link] for local_link in node_links
        }
        return node_links_dict


if __name__ == "__main__":
    example1 = {
        ("R1", "Eth0/0"): ("SW1", "Eth0/1"),
        ("R2", "Eth0/0"): ("SW1", "Eth0/2"),
        ("R2", "Eth0/1"): ("SW2", "Eth0/11"),
        ("R3", "Eth0/0"): ("SW1", "Eth0/3"),
        ("R4", "Eth0/0"): ("R3", "Eth0/1"),
        ("R5", "Eth0/0"): ("R3", "Eth0/2"),
        ("SW1", "Eth0/1"): ("R1", "Eth0/0"),
        ("SW1", "Eth0/2"): ("R2", "Eth0/0"),
        ("SW1", "Eth0/3"): ("R3", "Eth0/0"),
    }
    example2 = {("R1", "Eth0/4"): ("R7", "Eth0/0"), ("R1", "Eth0/6"): ("R9", "Eth0/0")}
    t1 = Topology(example1)

    pprint(f"{t1.topology=}")
    pprint(f"{t1[('SW1', 'Eth0/1')]=}")
    #    pprint(f"{t1[('SW123', 'Eth0/1')]=}")
    # t1[("R1", "Eth0/0")] = ("SW1", "Eth0/12")
    # pprint(f"{t1.topology}")
    t1[("R4", "Eth0/0")] = ("SW122", "Eth0/19")
    pprint(f"{t1.topology}")
    del t1[("R4", "Eth0/0")]
    #    del t1[("R445", "Eth0/0")]
    pprint(f"{t1.topology}")
# pprint(f"{iter(t1)=}")
# pprint(f"{t1.keys()=}")
# pprint(f"{t1.values()=}")
# pprint(f"{t1.items()=}")
# pprint(f"{t1.get(('R2', 'Eth0/0'))=}")
# pprint(f"{t1.pop(('R2', 'Eth0/0'))=}")
# t2 = Topology(example2)
# pprint(f"{t2.topology=}")
# t1.update(t2)
# pprint(f"{t1.topology}")
