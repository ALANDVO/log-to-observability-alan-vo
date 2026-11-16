import sys

def fix_file(path):
    with open(path, "r") as f:
        lines = f.readlines()
    # Find generate_dashboard function start index
    in_func = False
    added_import = False
    new_lines = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("def generate_dashboard("):
            in_func = True
        if in_func and stripped.startswith("arch = None"):
            # Insert import before arch = None or after we see arch = None
            # We'll insert before arch = None
            new_lines.append("    from app.models.schemas import ServiceNode, DatastoreNode\n")
            added_import = True
        # Replace type lines
        if in_func and "arch.services = [type('Node', (), s) for s in json.loads(r.services_json)]  # type: ignore" in line:
            indent = line[:len(line) - len(line.lstrip())]
            new_lines.append(f"{indent}arch.services = [ServiceNode(**s) for s in json.loads(r.services_json)]\n")
            continue
        if in_func and "arch.datastores = [type('DS', (), d) for d in json.loads(r.datastores_json)]  # type: ignore" in line:
            indent = line[:len(line) - len(line.lstrip())]
            new_lines.append(f"{indent}arch.datastores = [DatastoreNode(**d) for d in json.loads(r.datastores_json)]\n")
            continue
        # Keep other lines
        if not ("type('Node'" in line or "type('DS'" in line):
            new_lines.append(line)
    # Write back
    with open(path, "w") as f:
        f.writelines(new_lines)

if __name__ == "__main__":
    fix_file("backend/app/api/observability.py")
