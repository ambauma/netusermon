import pytest
import subprocess
import time
import os

# List of distributions to test
DISTROS = os.environ.get("NETUSERMON_TEST_DISTROS", "ubuntu-24.04,debian,fedora-40,ubi9").split(",")


def run_command(cmd, check=True):
    """Utility to run shell commands and return combined output."""
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if check and result.returncode != 0:
        pytest.fail(f"Command failed: {' '.join(cmd)}\nError Output:\n{result.stdout}")
    return result

@pytest.fixture(scope="module", params=DISTROS)
def container(request):
    distro = request.param
    image_tag = f"netusermon-test:{distro}"
    dockerfile = f"tests/integration/Dockerfile.{distro}"
    container_name = f"netusermon-test-{distro}"

    # 1. Build the image
    print(f"\nBuilding image for {distro}...")
    run_command(["docker", "build", "-t", image_tag, "-f", dockerfile, "."])

    # 2. Start the container
    print(f"Starting container {container_name}...")
    # Ensure any old container is removed
    subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)
    
    run_command([
        "docker", "run", "--detach", "--privileged", 
        "--name", container_name, image_tag
    ])

    # 3. Wait for the daemon to be ready
    print("Waiting for daemon to register on D-Bus...")
    max_retries = 20
    ready = False
    for _ in range(max_retries):
        logs = run_command(["docker", "logs", container_name]).stdout
        if "Daemon registered." in logs:
            ready = True
            break
        time.sleep(1)
    
    if not ready:
        logs = run_command(["docker", "logs", container_name]).stdout
        # Also try to grab the internal daemon log file if it exists
        daemon_logs = "Not available"
        try:
            daemon_logs = run_command(["docker", "exec", container_name, "cat", "/var/log/netusermon-daemon.log"], check=False).stdout
        except:
            pass
        subprocess.run(["docker", "rm", "-f", container_name])
        pytest.fail(f"Daemon failed to start in {distro}. \n--- Container Logs ---\n{logs}\n--- Internal Daemon Logs ---\n{daemon_logs}")

    yield container_name

    # 4. Cleanup
    print(f"\nCleaning up container {container_name}...")
    subprocess.run(["docker", "rm", "-f", container_name])

def test_daemon_behavior_on_distro(container):
    """Verifies daemon behavior by triggering activity and querying D-Bus from the host."""
    print(f"Triggering DNS activity in {container}...")
    
    # 1. Trigger DNS activity as 'testuser'
    run_command([
        "docker", "exec", "-u", "testuser",
        container,
        "curl", "-s", "http://example.com"
    ])
    
    # Give the daemon a moment to process
    time.sleep(2)
    
    # 2. Verify logs via D-Bus (busctl)
    print("Verifying logs via D-Bus...")
    result = run_command([
        "docker", "exec",
        container,
        "busctl", "call", "org.netusermon.Daemon", "/org/netusermon/Daemon", 
        "org.netusermon.Daemon", "GetLogs", "i", "5"
    ])
    
    # Assert that our test domain and user are in the D-Bus response
    assert "example.com" in result.stdout, f"Domain not found in D-Bus logs: {result.stdout}"
    assert "testuser" in result.stdout, f"User not found in D-Bus logs: {result.stdout}"
    
    # 3. Verify SQLite persistence and permissions (optional but good)
    print("Verifying SQLite file state...")
    # Ensure DB exists and is root-owned
    ls_result = run_command(["docker", "exec", container, "ls", "-l", "/var/lib/netusermon/data.db"])
    assert "root root" in ls_result.stdout, f"Database has incorrect ownership: {ls_result.stdout}"
    
    # Use sqlite3 CLI to check the table directly (black-box check of the data layer)
    sql_result = run_command([
        "docker", "exec",
        container,
        "sqlite3", "/var/lib/netusermon/data.db", "SELECT domain FROM dns_logs WHERE username='testuser';"
    ])
    assert "example.com" in sql_result.stdout, f"Domain not found in SQLite: {sql_result.stdout}"
    
    # 4. Test ClearLogs
    print("Testing ClearLogs via D-Bus...")
    run_command([
        "docker", "exec",
        container,
        "busctl", "call", "org.netusermon.Daemon", "/org/netusermon/Daemon", 
        "org.netusermon.Daemon", "ClearLogs"
    ])
    
    # Verify it's empty
    sql_empty_result = run_command([
        "docker", "exec",
        container,
        "sqlite3", "/var/lib/netusermon/data.db", "SELECT COUNT(*) FROM dns_logs;"
    ])
    assert "0" in sql_empty_result.stdout.strip(), "Database was not cleared"
    
    print(f"Integration tests PASSED on {container}")
