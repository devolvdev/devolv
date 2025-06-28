from pathlib import Path
from .core import validate_policy_file

def validate_policy_folder(folder_path: str) -> list:
    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        print(f"❌ Folder '{folder_path}' not found or is not a directory.")
        return [{"level": "error", "message": f"Folder '{folder_path}' not found or invalid."}]

    policy_files = list(folder.rglob("*.json")) + list(folder.rglob("*.yaml")) + list(folder.rglob("*.yml"))
    if not policy_files:
        print(f"⚠️ No policy files found in '{folder_path}'.")
        return [{"level": "warning", "message": f"No policy files found in '{folder_path}'."}]

    all_findings = []
    for file in policy_files:
        print(f"\n🔍 Validating: {file}")
        try:
            findings = validate_policy_file(str(file))
            if not findings:
                print("✅ Policy is valid.")
            else:
                all_findings.extend(findings)
        except Exception as e:
            all_findings.append({"level": "error", "message": f"{file.name} failed: {str(e)}"})
            print(f"❌ ERROR parsing {file.name}: {str(e)}")

    return all_findings
