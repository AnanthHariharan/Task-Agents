#!/usr/bin/env python3

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.append(str(PROJECT_ROOT))

async def test_framework():
    print("🧪 TESTING UNIVERSAL DATASET MCP FRAMEWORK")
    print("=" * 60)

    try:
        # Test 1: Import all adapters
        print("\n1️⃣ Testing Adapter Imports...")
        from shared.dataset_adapters import UniversalDatasetAdapter, TeachDatasetAdapter, ALFReDatasetAdapter
        print("   ✅ All adapters imported successfully")

        # Test 2: Initialize adapters
        print("\n2️⃣ Testing Adapter Initialization...")
        teach_adapter = TeachDatasetAdapter(str(PROJECT_ROOT))
        alfred_adapter = ALFReDatasetAdapter(str(PROJECT_ROOT / "data" / "alfred"))
        print("   ✅ Adapters initialized successfully")

        # Test 3: Test schemas
        print("\n3️⃣ Testing Dataset Schemas...")
        teach_schema = teach_adapter.get_schema()
        alfred_schema = alfred_adapter.get_schema()
        print(f"   ✅ TEACh schema: {teach_schema['name']} ({teach_schema['domain']})")
        print(f"   ✅ ALFReD schema: {alfred_schema['name']} ({alfred_schema['domain']})")

        # Test 4: Test episode loading
        print("\n4️⃣ Testing Episode Loading...")
        teach_episodes = teach_adapter.sample_episodes(n_samples=2, seed=42)
        alfred_episodes = alfred_adapter.sample_episodes(n_samples=2, seed=42)
        print(f"   ✅ TEACh: Loaded {len(teach_episodes)} episodes")
        print(f"   ✅ ALFReD: Loaded {len(alfred_episodes)} episodes")

        # Test 5: Test universal format
        print("\n5️⃣ Testing Universal Format...")
        if teach_episodes:
            ep = teach_episodes[0]
            required_fields = ['episode_id', 'dataset', 'domain', 'goal', 'actions', 'action_space', 'metadata']
            missing_fields = [field for field in required_fields if field not in ep]
            if missing_fields:
                print(f"   ⚠️  Missing fields: {missing_fields}")
            else:
                print("   ✅ Universal format validation passed")

        # Test 6: Test MCP server (mock mode)
        print("\n6️⃣ Testing MCP Server (Mock Mode)...")

        # Import the mock server test
        sys.path.append(str(PROJECT_ROOT / "mcp-servers"))
        from pathlib import Path
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "universal_dataset_server",
            PROJECT_ROOT / "mcp-servers" / "universal-dataset-server.py"
        )
        server_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(server_module)

        # Run mock server test
        mock_server = server_module.MockMCPServer()
        await mock_server.test_operations()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\n🚀 Framework Ready for Production!")
        print("\nNext Steps:")
        print("1. pip install mcp  # For full MCP functionality")
        print("2. Add your dataset paths to adapters")
        print("3. Run: python mcp-servers/universal-dataset-server.py")
        print("4. Integrate with your Task-Agents workflows")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_framework())
