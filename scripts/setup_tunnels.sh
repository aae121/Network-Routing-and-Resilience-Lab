#!/usr/bin/env bash
set -euo pipefail

R1=clab-routing-lab-r1
R4=clab-routing-lab-r4

create_tunnel() {
  local node="$1" name="$2" mode="$3" local_ip="$4" remote_ip="$5" inner_ip="$6"
  # Recreate an existing tunnel so this script can be run again safely.
  docker exec "$node" ip tunnel del "$name" 2>/dev/null || true
  docker exec "$node" ip tunnel add "$name" mode "$mode" local "$local_ip" remote "$remote_ip" ttl 64
  docker exec "$node" ip addr replace "$inner_ip" dev "$name"
  docker exec "$node" ip link set "$name" up
}

create_tunnel "$R1" gre1 gre 10.0.14.1 10.0.14.2 172.16.14.1/30
create_tunnel "$R4" gre1 gre 10.0.14.2 10.0.14.1 172.16.14.2/30
create_tunnel "$R1" ipip1 ipip 10.0.14.1 10.0.14.2 172.16.24.1/30
create_tunnel "$R4" ipip1 ipip 10.0.14.2 10.0.14.1 172.16.24.2/30

echo "GRE and IP-in-IP tunnels configured."
