import sys

with open('STATUS.md') as f:
    lines = f.readlines()
out = []
added = False
for line in lines:
    out.append(line)
    if line.strip() == '## Next round' and not added:
        out.append('\n')
        out.append('## Fixed items\n')
        out.append('- Fixed type mismatch in Observability API (backend/app/api/observability.py): replaced dynamic object construction with proper ServiceNode/DatastoreNode deserialization.\n')
        added = True
with open('STATUS.md', 'w') as f:
    f.writelines(out)
