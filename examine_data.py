import xarray as xr
import numpy as np

# Open the EMIT NetCDF dataset
ds = xr.open_dataset("emit_data/EMIT_L2B_MIN_001_20251002T064804_2527504_055.nc")

print("=== EMIT Data Structure Analysis ===")
print(f"\nDataset dimensions: {dict(ds.dims)}")

print(f"\nData variables:")
for var in ds.data_vars:
    print(f"  {var}: {ds[var].shape} - {ds[var].dtype}")

print(f"\nCoordinates:")
for coord in ds.coords:
    print(f"  {coord}: {ds.coords[coord].shape} - {ds.coords[coord].dtype}")

print(f"\nData value ranges:")
print(f"  group_1_band_depth: {ds['group_1_band_depth'].min().values:.3f} to {ds['group_1_band_depth'].max().values:.3f}")
print(f"  group_2_band_depth: {ds['group_2_band_depth'].min().values:.3f} to {ds['group_2_band_depth'].max().values:.3f}")
print(f"  group_1_mineral_id: {ds['group_1_mineral_id'].min().values} to {ds['group_1_mineral_id'].max().values}")
print(f"  group_2_mineral_id: {ds['group_2_mineral_id'].min().values} to {ds['group_2_mineral_id'].max().values}")

print(f"\nUnique minerals in group 1: {np.unique(ds['group_1_mineral_id'].values)}")
print(f"Unique minerals in group 2: {np.unique(ds['group_2_mineral_id'].values)}")

# Check if there are geographic coordinates
if 'latitude' in ds.coords and 'longitude' in ds.coords:
    print(f"\nGeographic extent:")
    print(f"  Latitude: {ds.coords['latitude'].min().values:.3f} to {ds.coords['latitude'].max().values:.3f}")
    print(f"  Longitude: {ds.coords['longitude'].min().values:.3f} to {ds.coords['longitude'].max().values:.3f}")

print(f"\nDataset attributes:")
for key, value in ds.attrs.items():
    print(f"  {key}: {str(value)[:100]}...")

ds.close()