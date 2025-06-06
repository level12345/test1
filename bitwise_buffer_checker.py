import re
import csv
from collections import defaultdict

# ✏️ CONFIG: List of buffer names you want to search
BUFFER_NAMES = ['high_buffer', 'medium_ascii_buffer', 'low_buffer']
CPP_FILE = "your_file.cpp"  # must exist in the same folder
OUTPUT_CSV = "buffer_collisions.csv"

# Generate regex pattern from buffer names
buffer_name_pattern = '|'.join(re.escape(name) for name in BUFFER_NAMES)
buffer_pattern = re.compile(
    rf'({buffer_name_pattern})\s*\[\s*(\d+)\s*\]\s*\[\s*(\d+)\s*\]\s*\.\s*([\w\.]+)\s*=\s*(.+);'
)

# Get bitmask based on union field format
def get_bitmask(union_field):
    if union_field in ('u32', 'f32'):
        return 0xFFFFFFFF
    if union_field.startswith('u16.'):
        if 'w0' in union_field:
            return 0x0000FFFF
        if 'w1' in union_field:
            return 0xFFFF0000
    if union_field.startswith('u8.'):
        match = re.match(r'u8\.b(\d)(?:\.n(\d))?', union_field)
        if match:
            byte = int(match.group(1))
            if match.group(2) is not None:
                bit = int(match.group(2))
                return 1 << (byte * 8 + bit)
            else:
                return 0xFF << (byte * 8)
    return 0

# Track assignments and conflicts
assignments = defaultdict(list)
bitmaps = defaultdict(int)

# Read and scan file
with open(CPP_FILE, 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    match = buffer_pattern.search(line)
    if match:
        buffer_name = match.group(1)
        frame = int(match.group(2))
        offset = int(match.group(3))
        union_field = match.group(4).strip()
        rhs = match.group(5).strip()
        line_number = i + 1

        key = (buffer_name, frame, offset)
        bitmask = get_bitmask(union_field)
        prior = bitmaps[key]
        overlap = (prior & bitmask) != 0

        assignments[key].append((union_field, rhs, line_number, overlap))
        bitmaps[key] |= bitmask

# Output to CSV
with open(OUTPUT_CSV, "w", newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Buffer", "Frame", "Offset", "Union Field(s)", "RHS Value(s)", "Line Numbers", "Overlapping Bits"])
    for key, entries in assignments.items():
        union_fields = "; ".join(e[0] for e in entries)
        rhs_values = "; ".join(e[1] for e in entries)
        line_nums = "; ".join(str(e[2]) for e in entries)
        conflict = "YES" if any(e[3] for e in entries) else ""
        writer.writerow([key[0], key[1], key[2], union_fields, rhs_values, line_nums, conflict])

print(f"✅ Scan complete. Output saved to {OUTPUT_CSV}")


#run commands
#python3 bitwise_buffer_checker.py
