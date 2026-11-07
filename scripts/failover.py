import subprocess
import time

router = "clab-routing-lab-r1"
destination = "10.0.23.2"
interface = "eth2"

print("Checking connectivity before failure")
subprocess.run(
    ["docker", "exec", router, "ping", "-c", "3", destination],
    check=True,
)

try:
    print("Taking down the direct R1-R3 link")
    subprocess.run(
        ["docker", "exec", router, "ip", "link", "set", interface, "down"],
        check=True,
    )

    print("Waiting 15 seconds for OSPF to update")
    time.sleep(15)

    print("Checking connectivity through the backup path")
    subprocess.run(
        ["docker", "exec", router, "ping", "-c", "3", destination],
        check=True,
    )
    subprocess.run(
        ["docker", "exec", router, "vtysh", "-c", "show ip route"],
        check=True,
    )
finally:
    print("Restoring the direct R1-R3 link")
    subprocess.run(
        ["docker", "exec", router, "ip", "link", "set", interface, "up"],
        check=True,
    )

    print("Waiting 15 seconds for OSPF to recover")
    time.sleep(15)

    subprocess.run(
        ["docker", "exec", router, "vtysh", "-c", "show ip route"],
        check=True,
    )
