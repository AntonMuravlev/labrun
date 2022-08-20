    sr_1_ports = ("1/1/c1", "1/1/c2","1/1/c3","1/1/c4","1/1/c5",) 
    network_port_template = """
       /configure/port[port-id={{port_id}}]/admin-state, enable
       /configure/port[port-id={{port_id}}]/connector/breakout, c1-100g
       /configure/port[port-id={{port_id}}/1]/admin-state, enable"""

    network_interface_template = (
        ("/configure/router[router-name=Base]/interface[interface-name={interface_name}]/admin-state", "enable"),
        ("/configure/router[router-name=Base]/interface[interface-name=to_P2]/ipv4/primary/address", "10.0.0.0"),
        ("/configure/router[router-name=Base]/interface[interface-name=to_P2]/ipv4/primary/prefix-length", "31")
    )
