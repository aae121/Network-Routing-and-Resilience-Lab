# Network Routing and Resilience Lab

<img width="1774" height="1282" alt="image" src="https://github.com/user-attachments/assets/d76017be-a596-4b45-8ce2-147deeb6de78" />


## Overview

This lab uses Containerlab, Linux, and FRRouting (FRR) to study how routers learn routes, choose paths, and recover after failures.

R1, R2, and R3 are in AS 65001. R4 is in AS 65002. OSPF and IS-IS exchange routes inside AS 65001. eBGP exchanges routes between the two ASes. The lab also tests GRE and IP-in-IP tunnels. Python scripts automate link and router failure checks.

## Topology

~~~text
                 AS 65001
            +----------------+
            |                |
            R1------R2       |
             \      / \      |
              \    /   \     |
               R3------------+
               | \          /
               |  \        /
          eBGP |   \eBGP  /
               |    \    /
               R4-----R1
                 AS 65002

R1-R2-R3 form an internal triangle.
R3-R4 and R1-R4 are external BGP links.
~~~

### Address plan

| Link or endpoint | Interfaces | Addresses |
|---|---|---|
| R1-R2 | R1 eth1 / R2 eth1 | 10.0.12.1/30 / 10.0.12.2/30 |
| R2-R3 | R2 eth2 / R3 eth1 | 10.0.23.1/30 / 10.0.23.2/30 |
| R1-R3 | R1 eth2 / R3 eth2 | 10.0.13.1/30 / 10.0.13.2/30 |
| R3-R4 | R3 eth3 / R4 eth1 | 10.0.34.1/30 / 10.0.34.2/30 |
| R1-R4 | R1 eth3 / R4 eth2 | 10.0.14.1/30 / 10.0.14.2/30 |
| R1 loopback | R1 lo | 10.1.0.1/32 |
| R4 loopback | R4 lo | 10.2.0.1/32 |
| GRE | R1 gre1 / R4 gre1 | 172.16.14.1/30 / 172.16.14.2/30 |
| IP-in-IP | R1 ipip1 / R4 ipip1 | 172.16.24.1/30 / 172.16.24.2/30 |

A /30 subnet has two usable IPv4 addresses and is used for router links. A /32 represents one host address. Loopbacks provide stable test endpoints.

## Routing concepts used

### OSPF and IS-IS

OSPF and IS-IS are interior gateway protocols. They share routes among routers inside one AS. Both run across the AS 65001 triangle so their neighbors and route calculations can be compared.

FRR marks OSPF routes with O and IS-IS routes with I. OSPF has administrative distance 110 and IS-IS has 115 in this lab, so OSPF normally wins when both protocols offer the same route to the main routing table. IS-IS routes can still be inspected separately.

### BGP and path selection

BGP exchanges routes between ASes. R4 learns the route to R1's loopback, 10.1.0.1/32, over both eBGP links. R4 gives local preference 200 to the path through R1 and 100 to the path through R3. Higher local preference is preferred, so the direct R1-R4 path is primary and R3 is the backup. Prefix lists control which routes neighbors can exchange.

A ping needs a route to its destination and a return route for the reply.

### Tunnels

GRE and IP-in-IP carry packets through logical tunnels over the R1-R4 underlay link, 10.0.14.0/30. The GRE inner network is 172.16.14.0/30. The IP-in-IP inner network is 172.16.24.0/30. Run the tunnel script after deployment or after restarting R1 or R4:

~~~bash
bash scripts/setup_tunnels.sh
~~~

## Files

~~~text
lab.clab.yml                 Containerlab nodes, links, and startup configs
configs/r1/frr.conf          R1 FRR configuration
configs/r2/frr.conf          R2 FRR configuration
configs/r3/frr.conf          R3 FRR configuration
configs/r4/frr.conf          R4 FRR configuration
scripts/failover.py          OSPF link-failure test
scripts/bgp_failover.py      BGP alternate-path test
scripts/router_failure.py    R3 stop/start test
scripts/setup_tunnels.sh     GRE and IP-in-IP setup
docs/images/                 README screenshots
~~~

## Requirements

- Ubuntu on WSL 2 or Linux
- Docker and Containerlab
- Python 3
- FRR image quay.io/frrouting/frr:containerlab-10.7.1

## Deploy

~~~bash
git clone https://github.com/aae121/network-routing-lab.git
cd network-routing-lab
containerlab deploy -t lab.clab.yml
containerlab inspect -t lab.clab.yml
bash scripts/setup_tunnels.sh
~~~

The topology references the saved FRR files in configs/. Containerlab loads them when it deploys each router. The tunnel script creates Linux tunnel interfaces separately.

Open a router command line:

~~~bash
docker exec -it clab-routing-lab-r1 vtysh
~~~

Useful route checks:

~~~bash
docker exec clab-routing-lab-r4 vtysh -c "show ip bgp 10.1.0.1/32"
docker exec clab-routing-lab-r1 vtysh -c "show ip route"
~~~

## Failure tests

Run these after deploying the lab and confirming baseline connectivity:

~~~bash
python3 scripts/failover.py
python3 scripts/bgp_failover.py
python3 scripts/router_failure.py
~~~

- failover.py disables the direct R1-R3 link, checks the OSPF path through R2, and restores the link.
- bgp_failover.py disables the preferred R1-R4 link, checks the backup BGP path through R3, tests reachability, and restores the link.
- router_failure.py stops R3, checks reachability over the direct R1-R4 path, and starts R3 again.

Each script uses a finally block to restore the link or router if a check fails. Routing protocols need time to converge, so a brief interruption is possible.

## Results observed

- OSPF neighbors reached Full state across R1, R2, and R3.
- The OSPF link-failure test kept its ping at 0% loss and showed traffic using R2 while R1-R3 was down.
- IS-IS neighbors reached Up state. During a link failure, R2's IS-IS route to R1 used R3.
- R4 learned two BGP paths to 10.1.0.1/32 and preferred R1 with local preference 200 over R3 with 100.
- The manual BGP link-failure test and R3 router-failure test each kept the tested ping at 0% loss.
- GRE and IP-in-IP endpoint pings each succeeded with 0% loss.

These results describe the observed lab run. Timers and route output can vary as the protocols converge.

## Stop and remove

Stop nodes but keep the lab definition:

~~~bash
containerlab stop -t lab.clab.yml
~~~

Start stopped nodes:

~~~bash
containerlab start -t lab.clab.yml
~~~

Remove the lab containers and links:

~~~bash
containerlab destroy -t lab.clab.yml
~~~

The files in this repository are the source used to recreate the lab.
