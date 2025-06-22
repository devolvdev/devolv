from pathlib import Path
from .core import validate_policy_file   # ✅ reusing logic from core.py

def validate_policy_folder(folder_path: str) -> int:
    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        print(f"❌ Folder '{folder_path}' not found or is not a directory.")
        return 1

    policy_files = list(folder.rglob("*.json")) + list(folder.rglob("*.yaml")) + list(folder.rglob("*.yml"))
    if not policy_files:
        print(f"⚠️ No policy files found in '{folder_path}'.")
        return 1

    has_errors = False
    for file in policy_files:
        print(f"\n🔍 Validating: {file}")
        try:
            findings = validate_policy_file(str(file))  # ✅ core logic used here
            if not findings:
                print("✅ Policy is valid.")
            else:
                has_errors = True
                for f in findings:
                    print(f"❌ {f['level'].upper()}: {f['message']}")
        except Exception as e:
            has_errors = True
            print(f"❌ ERROR parsing {file.name}: {str(e)}")

    return 1 if has_errors else 0
