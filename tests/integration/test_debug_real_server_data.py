#!/usr/bin/env python3
"""
Debug why get_message_for_bus() returns {} with real server.

This investigates what data actually exists in the database when the server is running
and why the GridAPPSD adapter can't find it.
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import Mock

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import ieee_2030_5.adapters as adpt
import ieee_2030_5.models as m

# Test configuration
SERVER_URL = "https://localhost:5000"
TEST_CERT_CN = "_CA0A0024-DA79-4395-9B05-6A7B9DE0AED9"
TLS_DIR = Path.home() / "tls"
EXPECTED_LFDI = "8c0caca6961d3ddb1faca475cd14ec6df32c846a"

TEST_DER_STATUS_XML = """<DERStatus xmlns="urn:ieee:std:2030.5:ns">
  <readingTime>1755670000</readingTime>
  <stateOfChargeStatus>
    <dateTime>-2209075200</dateTime>
    <value>7500</value>
  </stateOfChargeStatus>
</DERStatus>"""


def debug_real_server_data():
    """Debug what data exists and why adapter can't find it."""
    print("\n🔍 Debugging Real Server Data Issues")
    print("=" * 50)

    # Clear database lock
    lock_file = Path.home() / ".ieee_2030_5_data" / "points.fs.lock"
    if lock_file.exists():
        lock_file.unlink()
        print("🔓 Cleared database lock")

    # Start server
    print("\n🚀 Starting server...")
    os.chdir(project_root)
    process = subprocess.Popen(
        ["2030_5_server", str(project_root / "config.yml")],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        preexec_fn=os.setsid,
    )

    print(f"📡 Server started (PID: {process.pid})")

    try:
        # Wait briefly for server initialization
        print("⏳ Waiting for server initialization...")
        time.sleep(10)

        # Store test data directly (simulate what HTTP PUT would do)
        print("\n1️⃣ Storing test data directly...")
        test_uri = "/der_debug_test_ders"

        der_status = m.DERStatus(
            href=test_uri,
            readingTime=1755670000,
            stateOfChargeStatus=m.StateOfChargeStatusType(dateTime=-2209075200, value=7500),
        )

        result = adpt.get_list_adapter().set_single(test_uri, der_status, EXPECTED_LFDI)
        print(f"Storage result: {result.success}")
        if not result.success:
            print(f"❌ Failed to store: {result}")
            return

        # Step 1: Debug what's actually in the database
        print("\n2️⃣ Examining database contents...")

        # Check all URIs that end with 'ders'
        def detect_ders(uri_key):
            return uri_key and uri_key.endswith("ders")

        all_ders_uris = adpt.get_list_adapter().filter_single_dict(detect_ders)
        print(f"📊 Found {len(all_ders_uris)} URIs ending with 'ders': {all_ders_uris}")

        # Check all URIs in database
        def get_all_uris(uri_key):
            return uri_key is not None

        all_uris = adpt.get_list_adapter().filter_single_dict(get_all_uris)
        print(f"📊 Found {len(all_uris)} total URIs: {all_uris[:10]}...")  # Show first 10

        # Step 2: Check metadata for each DERStatus
        print("\n3️⃣ Examining DERStatus metadata...")
        for uri in all_ders_uris:
            try:
                stored_data = adpt.get_list_adapter().get_single(uri)
                metadata = adpt.get_list_adapter().get_single_meta_data(uri)

                print(f"📋 URI: {uri}")
                print(f"  - Type: {type(stored_data).__name__}")
                print(f"  - LFDI: {metadata.get('lfdi', 'N/A')}")
                print(
                    f"  - SOC Value: {stored_data.stateOfChargeStatus.value if stored_data.stateOfChargeStatus else 'N/A'}"
                )
                print(f"  - Reading Time: {stored_data.readingTime}")

            except Exception as e:
                print(f"❌ Error reading {uri}: {e}")

        # Step 3: Test GridAPPSD adapter filtering
        print("\n4️⃣ Testing GridAPPSD adapter filtering...")

        try:
            from ieee_2030_5.adapters.gridappsd_adapter import GridAPPSDAdapter, HouseLookup

            # Create adapter with different inverter configurations to test matching
            mock_gapps = Mock()
            mock_gapps.connected = True

            os.environ["GRIDAPPSD_SIMULATION_ID"] = "debug_test"
            os.environ["GRIDAPPSD_SERVICE_NAME"] = "debug_service"

            adapter = GridAPPSDAdapter(
                gapps=mock_gapps,
                gridappsd_configuration={
                    "field_bus_def": {"id": "debug_bus"},
                    "publish_interval_seconds": 3,
                    "house_named_inverters_regex": None,
                    "utility_named_inverters_regex": None,
                    "model_name": "debug_model",
                    "default_pin": "123456",
                },
                tls=Mock(),
            )

            # Test with no inverters
            adapter._inverters = []
            print("\n🔧 Testing with no inverters...")
            message = adapter.get_message_for_bus()
            print(f"Result: {message}")

            # Test with inverter that has our LFDI
            print("\n🔧 Testing with matching LFDI inverter...")
            adapter._inverters = [HouseLookup(mRID="debug_house", name="DebugHouse", lfdi=EXPECTED_LFDI)]
            message = adapter.get_message_for_bus()
            print(f"Result: {message}")

            # Test with different LFDI to see difference
            print("\n🔧 Testing with non-matching LFDI...")
            adapter._inverters = [HouseLookup(mRID="other_house", name="OtherHouse", lfdi="different_lfdi_12345")]
            message = adapter.get_message_for_bus()
            print(f"Result: {message}")

            # Step 4: Manual simulation of get_message_for_bus logic
            print("\n5️⃣ Manually simulating get_message_for_bus logic...")

            # Reset to our test inverter
            adapter._inverters = [HouseLookup(mRID="manual_test_house", name="ManualTestHouse", lfdi=EXPECTED_LFDI)]

            # Step by step what get_message_for_bus does:
            print("Step 1: Filter for DERStatus URIs...")
            der_status_uris = adpt.get_list_adapter().filter_single_dict(lambda k: detect_ders(k))
            print(f"  Found: {der_status_uris}")

            print("Step 2: Process each URI...")
            for uri_key in der_status_uris:
                try:
                    print(f"  Processing: {uri_key}")

                    # Get metadata and check LFDI
                    meta = adpt.get_list_adapter().get_single_meta_data(uri_key)
                    print(f"    Metadata LFDI: {meta.get('lfdi')}")

                    # Check if any inverter matches this LFDI
                    matching_inverter = None
                    for inverter in adapter._inverters:
                        print(f"    Checking inverter LFDI: {inverter.lfdi}")
                        if inverter.lfdi == meta.get("lfdi"):
                            matching_inverter = inverter
                            print("    ✅ Match found!")
                            break

                    if matching_inverter:
                        # Get the DERStatus data
                        status = adpt.get_list_adapter().get_single(uri_key)
                        print(f"    DERStatus SOC: {status.stateOfChargeStatus.value}")
                        print(f"    DERStatus Time: {status.readingTime}")

                        # This should create a message entry
                        print(f"    ✅ Should create message entry for {matching_inverter.mRID}")
                    else:
                        print("    ❌ No matching inverter found")

                except Exception as e:
                    print(f"    ❌ Error processing {uri_key}: {e}")

            print("\n6️⃣ Final get_message_for_bus() call...")
            final_message = adapter.get_message_for_bus()
            print(f"Final result: {final_message}")

        except ImportError:
            print("⚠️  GridAPPSD adapter not available")
        except Exception as e:
            print(f"❌ Error testing adapter: {e}")
            import traceback

            traceback.print_exc()

    finally:
        # Stop server
        print("\n🛑 Stopping server...")
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=10)
            print("✅ Server stopped")
        except:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                process.wait()
            except:
                pass


if __name__ == "__main__":
    debug_real_server_data()
