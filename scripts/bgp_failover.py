import subprocess
import time

r1 = "clab-routing-lab-r1"
r4 = "clab-routing-lab-r4"

print("Checking reachability before failure")
subprocess.run(
    ["docker", "exec", r4, "ping", "-I", "10.2.0.1", "-c", "3", "10.1.0.1"],
    check=True,
)

try:
    print("Taking the preferred R1-R4 link down")
    subprocess.run(
        ["docker", "exec", r1, "ip", "link", "set", "eth3", "down"],
        check=True,
    )

    print("Waiting 15 seconds for BGP to update")
    time.sleep(15)

    result = subprocess.run(
        ["docker", "exec", r4, "vtysh", "-c", "show ip bgp 10.1.0.1/32"],
        check=True,
        text=True,
        capture_output=True,
    )
    print(result.stdout)

    if "10.0.34.1" not in result.stdout:
        raise RuntimeError("R4 did not show the backup path through R3")

    print("Checking reachability through the backup path")
    subprocess.run(
        ["docker", "exec", r4, "ping", "-I", "10.2.0.1", "-c", "3", "10.1.0.1"],
        check=True,
    )
finally:
    print("Restoring the R1-R4 link")
    subprocess.run(
        ["docker", "exec", r1, "ip", "link", "set", "eth3", "up"],
        check=True,
    )

    time.sleep(15)
    result = subprocess.run(
        ["docker", "exec", r4, "vtysh", "-c", "show ip bgp 10.1.0.1/32"],
        check=True,
        text=True,
        capture_output=True,
    )
    print("Route after recovery:")
    print(result.stdout)
