
import sys
from netCDF4 import Dataset
import numpy as np

def decode_chararray(arr):
    """
    Decode netCDF char arrays or variable-length strings robustly to python strings.
    arr may be: (N, M) array of bytes (S1), or (N,) array of variable-length bytes/strings.
    """
    if arr.dtype.kind in ('S','V','O'):
        # char array -> join bytes in each row
        names = []
        for row in arr:
            # row could be an array of bytes
            try:
                # try joining if row is sequence of bytes
                joined = b''.join([(bytes([c]) if isinstance(c, int) else c) for c in row])
                s = joined.decode('utf-8', errors='ignore').strip()
            except Exception:
                # fallback
                try:
                    s = ''.join([c.decode('utf-8', errors='ignore') if isinstance(c, (bytes, bytearray)) else str(c) for c in row]).strip()
                except Exception:
                    s = str(row).strip()
            names.append(s)
        return names
    else:
        # likely already string dtype or numpy unicode
        return [str(x).strip() for x in arr[:]]

def main(fname):
    nc = Dataset(fname, 'r')
    print("Top-level groups:", list(nc.groups.keys()))
    if 'mineral_metadata' not in nc.groups:
        raise SystemExit("No 'mineral_metadata' group found in this file. Is this an EMIT L2B MIN file?")

    mm = nc.groups['mineral_metadata']
    print("Variables in mineral_metadata:", list(mm.variables.keys()))

    # Get names
    if 'mineral_name' in mm.variables:
        mnames_raw = mm.variables['mineral_name'][:]
        mnames = decode_chararray(mnames_raw)
    elif 'name' in mm.variables:
        mnames = decode_chararray(mm.variables['name'][:])
    else:
        raise SystemExit("Couldn't find 'mineral_name' or 'name' variable in mineral_metadata")

    # index (should be 1-based), group, record if present
    idx = mm.variables['index'][:] if 'index' in mm.variables else np.arange(1, len(mnames)+1)
    grp = mm.variables['group'][:] if 'group' in mm.variables else np.zeros_like(idx)

    # Print mapping (index -> name, group)
    print("\nMineral lookup (index -> group -> name). Note: 0 in the scene data == No_Match.\n")
    for i, g, nm in zip(idx, grp, mnames):
        print(f"{int(i):3d}   group:{int(g):2d}   {nm}")

    # simple check: how many unique IDs appear in group_1_mineral_id
    # open root variables safely
    if 'group_1_mineral_id' in nc.variables:
        g1 = nc.variables['group_1_mineral_id'][:]
    else:
        # root variables are often at dataset root -> use nc.variables keys
        g1 = None

    # close
    nc.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python extract_mineral_lookup.py /path/to/EMIT_L2B_MIN_...nc")
        sys.exit(1)
    main(sys.argv[1])