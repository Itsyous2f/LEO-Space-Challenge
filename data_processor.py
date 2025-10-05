import xarray as xr
import numpy as np
import json
from pathlib import Path
from netCDF4 import Dataset

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

def extract_mineral_names_from_netcdf(file_path):
    """Extract actual mineral names from the NetCDF file's mineral_metadata group"""
    try:
        nc = Dataset(file_path, 'r')
        
        if 'mineral_metadata' not in nc.groups:
            print(f"Warning: No 'mineral_metadata' group found in {file_path}")
            return {}
        
        mm = nc.groups['mineral_metadata']
        
        # Get mineral names
        if 'name' in mm.variables:
            mnames_raw = mm.variables['name'][:]
            mnames = decode_chararray(mnames_raw)
        elif 'mineral_name' in mm.variables:
            mnames_raw = mm.variables['mineral_name'][:]
            mnames = decode_chararray(mnames_raw)
        else:
            print(f"Warning: No 'name' or 'mineral_name' variable found in mineral_metadata")
            return {}
        
        # Get indices (should be 1-based)
        idx = mm.variables['index'][:] if 'index' in mm.variables else np.arange(1, len(mnames)+1)
        
        # Get groups
        grp = mm.variables['group'][:] if 'group' in mm.variables else np.zeros_like(idx)
        
        # Create mapping
        mineral_mapping = {}
        for i, g, nm in zip(idx, grp, mnames):
            # Clean up the mineral name - remove technical codes but keep main name
            clean_name = nm.split(' ')[0]  # Take first word for cleaner display
            if clean_name.endswith('_'):
                clean_name = clean_name[:-1]
            
            # For better readability, replace underscores with spaces
            clean_name = clean_name.replace('_', ' ')
            
            mineral_mapping[int(i)] = clean_name
        
        nc.close()
        return mineral_mapping
        
    except Exception as e:
        print(f"Error extracting mineral names from {file_path}: {e}")
        return {}

def process_emit_data():
    """Process EMIT data and convert to web-friendly formats"""
    
    
    files = [
        "emit_data/EMIT_L2B_MIN_001_20251002T064804_2527504_055.nc",
        "emit_data/EMIT_L2B_MIN_001_20251002T064816_2527504_056.nc"
    ]
    
    processed_data = []
    
    for i, file_path in enumerate(files):
        print(f"Processing {file_path}...")
        ds = xr.open_dataset(file_path)
        
        # Get data arrays
        bd1 = ds["group_1_band_depth"].values
        bd2 = ds["group_2_band_depth"].values
        gid1 = ds["group_1_mineral_id"].values
        gid2 = ds["group_2_mineral_id"].values
        
        # Create summary statistics
        summary = {
            "file_index": i,
            "filename": Path(file_path).name,
            "time_start": ds.attrs.get("time_coverage_start", ""),
            "time_end": ds.attrs.get("time_coverage_end", ""),
            "spatial_extent": {
                "north": float(ds.attrs.get("northernmost_latitude", 0)),
                "south": float(ds.attrs.get("southernmost_latitude", 0)),
                "east": float(ds.attrs.get("easternmost_longitude", 0)),
                "west": float(ds.attrs.get("westernmost_longitude", 0))
            },
            "dimensions": {
                "downtrack": int(ds.sizes["downtrack"]),
                "crosstrack": int(ds.sizes["crosstrack"])
            },
            "group1_minerals": np.unique(gid1[gid1 != 0]).astype(int).tolist(),
            "group2_minerals": np.unique(gid2[gid2 != 0]).astype(int).tolist(),
            "band_depth_stats": {
                "group1": {
                    "min": float(bd1[gid1 != 0].min()) if np.any(gid1 != 0) else 0,
                    "max": float(bd1[gid1 != 0].max()) if np.any(gid1 != 0) else 0,
                    "mean": float(bd1[gid1 != 0].mean()) if np.any(gid1 != 0) else 0,
                    "pixels_with_minerals": int(np.sum(gid1 != 0))
                },
                "group2": {
                    "min": float(bd2[gid2 != 0].min()) if np.any(gid2 != 0) else 0,
                    "max": float(bd2[gid2 != 0].max()) if np.any(gid2 != 0) else 0,
                    "mean": float(bd2[gid2 != 0].mean()) if np.any(gid2 != 0) else 0,
                    "pixels_with_minerals": int(np.sum(gid2 != 0))
                }
            }
        }
        
        # downsample data for web proformance
        downsample_factor = 10
        bd1_ds = bd1[::downsample_factor, ::downsample_factor]
        bd2_ds = bd2[::downsample_factor, ::downsample_factor]
        gid1_ds = gid1[::downsample_factor, ::downsample_factor]
        gid2_ds = gid2[::downsample_factor, ::downsample_factor]
        
        
        viz_data = {
            "downsampled_shape": [bd1_ds.shape[0], bd1_ds.shape[1]],
            "group1_band_depth": bd1_ds.tolist(),
            "group1_mineral_id": gid1_ds.astype(int).tolist(),
            "group2_band_depth": bd2_ds.tolist(),
            "group2_mineral_id": gid2_ds.astype(int).tolist()
        }
        
        processed_data.append({
            "summary": summary,
            "visualization_data": viz_data
        })
        
        ds.close()
    
    return processed_data

def create_mineral_mapping():
    """Create a mapping of mineral IDs to actual mineral names from the NetCDF files"""
    
    # Try to extract mineral names from the first NetCDF file
    files = [
        "emit_data/EMIT_L2B_MIN_001_20251002T064804_2527504_055.nc",
        "emit_data/EMIT_L2B_MIN_001_20251002T064816_2527504_056.nc"
    ]
    
    # Extract from the first file
    mineral_mapping = extract_mineral_names_from_netcdf(files[0])
    
    # If that fails, try the second file
    if not mineral_mapping:
        mineral_mapping = extract_mineral_names_from_netcdf(files[1])
    
    # If we still don't have mineral names, provide a fallback
    if not mineral_mapping:
        print("Warning: Could not extract mineral names from NetCDF files, using fallback mapping")
        # Add some basic fallback names
        mineral_mapping = {
            0: "No Match",
            # Add more as needed based on your data
        }
    
    return mineral_mapping

def main():
    print("Processing EMIT data for web visualization...")
    
    # Process the data
    processed_data = process_emit_data()
    
   
    mineral_mapping = create_mineral_mapping()
    
   
    output_data = {
        "metadata": {
            "generated": "2025-10-05",
            "description": "EMIT L2B Mineral Data for Web Visualization",
            "total_files": len(processed_data),
            "downsample_factor": 10
        },
        "mineral_mapping": mineral_mapping,
        "datasets": processed_data
    }
    
    
    with open("web_data.json", "w") as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Data processing complete!")
    print(f"Generated web_data.json with {len(processed_data)} datasets")
    print(f"File size: {Path('web_data.json').stat().st_size / 1024 / 1024:.2f} MB")
    
    
    sample_data = {
        "metadata": output_data["metadata"],
        "mineral_mapping": mineral_mapping,
        "datasets": [processed_data[0]] 
    }
    
    with open("web_data_sample.json", "w") as f:
        json.dump(sample_data, f, indent=2)
    
    print(f"Also created web_data_sample.json (smaller file for testing)")

if __name__ == "__main__":
    main()