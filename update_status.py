import sys

def update_status(path):
    with open(path, "r") as f:
        lines = f.readlines()
    # Find line index for "## Outstanding findings"
    start_idx = None
    for i, line in enumerate(lines):
        if line.strip() == "## Outstanding findings":
            start_idx = i
            break
    if start_idx is None:
        # If not found, just append at end before the final blank line
        new_lines = lines + ["\n## Fixed items\n", "- Fixed type mismatch in Observability API (backend/app/api/observability.py): replaced dynamic object construction with proper ServiceNode/DatastoreNode deserialization.\n"]
        with open(path, "w") as f:
            f.writelines(new_lines)
    else:
        # Insert after the "## Outstanding findings" line (maybe after one line)
        insert_idx = start_idx + 1
        lines.insert(insert_idx, "\n## Fixed items\n")
        lines.insert(insert_idx +  special handling for line modifications
        # Actually we need to preserve existing content; we'll just append after the header.
        # Instead, we can simply add a new heading after the "## Outstanding findings" block.
        # For simplicity, we'll just append at end before the final blank line.
        pass
    # Simpler: append at end before final blank line
    out = []
    for line in lines:
        out.append(line)
        if line.strip() == "" and "## Fixed items" not in out:
            # Insert before this blank line?
            pass
    # Let's just simply append at the end before the final blank line (if any)
    # We'll just append after the last non-blank line.
    final_lines = [line.rstrip("\n") for line in lines if line.strip() != ""]
    # Append new section
    final_lines.append("")
    final_lines.append("## Fixed items")
    final_lines.append("- Fixed type mismatch in Observability API (backend/app/api/observability.py): replaced dynamic object construction with proper ServiceNode/DatastoreNode deserialization.")
    with open(path, "w") as f:
        f.write("\n".join(final_lines) + "\n")
