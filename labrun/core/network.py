import ipaddress


class IPv4Network:
    @classmethod
    def __get_validators__(cls):
        # one or more validators may be yielded which will be called in the
        # order to validate the input, each validator will receive as an input
        # the value returned from the previous validator
        yield cls.validate

    @classmethod
    def validate(cls, value):
        try:
            _net = ipaddress.ip_network(value)
        except ValueError as error:
            raise ValueError(f"IP prefix validation is failed\n{error}")
        return cls(value)

    def __init__(self, network):
        _net = ipaddress.ip_network(network)
        self.network = network
        self.network_address = str(_net.network_address)
        self.hosts = tuple(
            [self.network_address]
            + [str(h) for h in _net.hosts()]
            + [str(_net.broadcast_address)],
        )
        self.allocated = set()
        self.unassigned = set(self.hosts)
        self.p2p_networks = {}

    def __str__(self):
        return f"IPv4Network {self.network}"

    def __repr__(self):
        return f"IPv4Network({self.network})"

    def __getitem__(self, item):
        return self.hosts[item]

    def __len__(self):
        return len(self.hosts)

    def __contains__(self, value):
        return True if value in self.hosts else False

    def __iter__(self):
        return iter(self.hosts)

    def count(self, value):
        return self.hosts.count(value)

    def index(self, value):
        return self.hosts.index(value)

    def allocate_ip(self, ip):
        if ip in self.hosts and ip not in self.allocated:
            self.allocated.add(ip)
            self.unassigned.remove(ip)
        else:
            raise ValueError

    def free_ip(self, ip):
        if ip in self.hosts and ip in self.allocated:
            self.allocated.remove(ip)
            self.unassigned.add(ip)
        else:
            raise ValueError

    def allocate_p2p_network(self, local_side, remote_side):
        link_name = (local_side, remote_side)
        self.p2p_networks[link_name] = (
            self.allocate_next_free_ip(),
            self.allocate_next_free_ip(),
        )
        first_address_in_network = self.p2p_networks[link_name][0]
        return first_address_in_network

    def allocate_next_free_ip(self, loopback=False):
        for host in self.hosts:
            if loopback and (host == self.network_address):
                continue
            if host not in self.allocated:
                next_free_ip = host
                self.allocate_ip(next_free_ip)
                return next_free_ip

    def find_p2p_address(self, local_side, remote_side):
        for link in self.p2p_networks.keys():
            if local_side == link[0] and remote_side == link[1]:
                return self.p2p_networks[link][0]
            elif local_side == link[1] and remote_side == link[0]:
                return self.p2p_networks[link][1]
