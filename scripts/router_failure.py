import subprocess
import time

topology = "lab.clab.yml"
r4 = "clab-routing-lab-r4"

def run(command, capture=False):
    return subprocess.run(
        command,
        check=True,
        text=True,
        capture_output=capture,
    )

print("Checking reachability before failure")
run(
    ["docker", "exec", r4, "ping", "-I", "10.2.0.1", "-c", "3", "10.1.0.1"]
)

try:
    print("Stopping router R3")
    run(["clab", "stop", "-t", topology, "--node", "r3"])
    time.sleep(15)

    result = run(
        ["docker", "exec", r4, "vtysh", "-c", "show ip bgp 10.1.0.1/32"],
        capture=True,
    )
    print(result.stdout)

    if "10.0.14.1" not in result.stdout:
        raise RuntimeError("R4 did not select the direct path through R1")

    print("Checking reachability while R3 is stopped")
    run(
        ["docker", "exec", r4, "ping", "-I", "10.2.0.1", "-c", "3", "10.1.0.1"]
    )
finally:
    print("Starting R3 again")
    run(["clab", "start", "-t", topology, "--node", "r3"])
    time.sleep(15)
