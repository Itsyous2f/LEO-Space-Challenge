import sys
from netCDF4 import Dataset
import numpy as np

def decode_chararray(arr):
    """
    Decode netCDF char arrays or variable-length strings robustly to python strings.
    """
    if arr.dtype.kind in ('S','V','O'):
        names = []
        for row in arr:
            try:
                joined = b''.join([(bytes([c]) if isinstance(c, int) else c) for c in row])
                s = joined.decode('utf-8', errors='ignore').strip()
            except Exception:
                try:
                    s = ''.join([c.decode('utf-8', errors='ignore') if isinstance(c, (bytes, bytearray)) else str(c) for c in row]).strip()
                except Exception:
                    s = str(row).strip()
            names.append(s)
        return names
    else:
        return [str(x).strip() for x in arr[:]]

def analyze_groups(fname):
    nc = Dataset(fname, 'r')
    
    if 'mineral_metadata' not in nc.groups:
        raise SystemExit("No 'mineral_metadata' group found in this file.")

    mm = nc.groups['mineral_metadata']
    
    # Get names and groups
    mnames_raw = mm.variables['name'][:]
    mnames = decode_chararray(mnames_raw)
    
    idx = mm.variables['index'][:]
    grp = mm.variables['group'][:]
    
    # Analyze groups
    group1_minerals = []
    group2_minerals = []
    
    for i, g, nm in zip(idx, grp, mnames):
        if int(g) == 1:
            group1_minerals.append((int(i), nm))
        elif int(g) == 2:
            group2_minerals.append((int(i), nm))
    
    print("=" * 80)
    print("EMIT MINERAL GROUP ANALYSIS")
    print("=" * 80)
    
    print(f"\n📊 GROUP SUMMARY:")
    print(f"   Group 1: {len(group1_minerals)} minerals")
    print(f"   Group 2: {len(group2_minerals)} minerals")
    print(f"   Total: {len(group1_minerals) + len(group2_minerals)} minerals")
    
    print(f"\n🔬 GROUP 1 CHARACTERISTICS:")
    print("   Primary minerals detected in this group:")
    
    # Analyze Group 1 mineral types
    g1_types = {}
    for idx, name in group1_minerals[:20]:  # Show first 20
        # Extract mineral type (first word)
        mineral_type = name.split()[0].replace('_', ' ')
        if mineral_type in g1_types:
            g1_types[mineral_type] += 1
        else:
            g1_types[mineral_type] = 1
        print(f"   {idx:3d}: {name}")
    
    print("\n   Common mineral types in Group 1:")
    for mineral_type, count in sorted(g1_types.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   - {mineral_type}: {count} variations")
    
    print(f"\n🔬 GROUP 2 CHARACTERISTICS:")
    print("   Primary minerals detected in this group:")
    
    # Analyze Group 2 mineral types
    g2_types = {}
    for idx, name in group2_minerals[:20]:  # Show first 20
        mineral_type = name.split()[0].replace('_', ' ')
        if mineral_type in g2_types:
            g2_types[mineral_type] += 1
        else:
            g2_types[mineral_type] = 1
        print(f"   {idx:3d}: {name}")
    
    print("\n   Common mineral types in Group 2:")
    for mineral_type, count in sorted(g2_types.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   - {mineral_type}: {count} variations")
    
    # Check what minerals are actually detected in the scene
    print(f"\n🌍 MINERALS DETECTED IN THIS SCENE:")
    
    # Get the actual mineral IDs detected in the scene
    g1_detected = set()
    g2_detected = set()
    
    if 'group_1_mineral_id' in nc.variables:
        g1_ids = nc.variables['group_1_mineral_id'][:]
        g1_detected = set(np.unique(g1_ids[g1_ids > 0]).astype(int))
        
    if 'group_2_mineral_id' in nc.variables:
        g2_ids = nc.variables['group_2_mineral_id'][:]
        g2_detected = set(np.unique(g2_ids[g2_ids > 0]).astype(int))
    
    print(f"   Group 1 minerals detected: {len(g1_detected)}")
    for mineral_id in sorted(list(g1_detected))[:10]:  # Show first 10
        mineral_name = next((name for idx, name in group1_minerals if idx == mineral_id), f"Unknown_{mineral_id}")
        print(f"   - ID {mineral_id}: {mineral_name}")
    
    print(f"\n   Group 2 minerals detected: {len(g2_detected)}")
    for mineral_id in sorted(list(g2_detected))[:10]:  # Show first 10
        mineral_name = next((name for idx, name in group2_minerals if idx == mineral_id), f"Unknown_{mineral_id}")
        print(f"   - ID {mineral_id}: {mineral_name}")
    
    print(f"\n📍 GEOGRAPHIC CONTEXT:")
    print(f"   Latitude range: {nc.getncattr('southernmost_latitude'):.3f}° to {nc.getncattr('northernmost_latitude'):.3f}°")
    print(f"   Longitude range: {nc.getncattr('westernmost_longitude'):.3f}° to {nc.getncattr('easternmost_longitude'):.3f}°")
    print(f"   Time: {nc.getncattr('time_coverage_start')}")
    
    nc.close()

if __name__ == '__main__':
    analyze_groups("emit_data/EMIT_L2B_MIN_001_20251002T064804_2527504_055.nc")