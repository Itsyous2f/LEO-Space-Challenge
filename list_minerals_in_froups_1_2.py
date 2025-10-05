import xarray as xr
import numpy as np

ds = xr.open_dataset("emit_data/EMIT_L2B_MIN_001_20251002T064804_2527504_055.nc")
gid1 = ds["group_1_mineral_id"].values
gid2 = ds["group_2_mineral_id"].values

print("Unique minerals in group 1:", np.unique(gid1))
print("Unique minerals in group 2:", np.unique(gid2))
