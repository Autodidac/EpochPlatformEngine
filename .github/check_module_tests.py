from pathlib import Path
import sys

text = (Path(sys.argv[1]) / "CTestTestfile.cmake").read_text()
required = ["EpochPlatformModuleContractStatic", "EpochPlatformModuleContractShared",
            "EpochPlatformEngineTests", "epoch_platform_policy_contract",
            "epoch_platform_tier_contract", "epoch_platform_native_input_contract",
            "epoch_platform_entry_contract"]
missing = [name for name in required if name not in text]
if missing:
    raise SystemExit("Missing canonical/module CPU contracts: " + ", ".join(missing))
print("All seven canonical native/module/adapter CPU contracts registered")
