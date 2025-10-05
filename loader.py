import earthaccess

# Login (interactive or using .netrc)
auth = earthaccess.login(strategy="interactive")

# Search for EMIT L2B mineral data (global, all time)
granules = earthaccess.search_data(
    short_name="EMITL2BMIN",
    version="001",
    temporal=("2025-09-25", "2025-10-04")
)

print(f"Total granules found: {len(granules)}")

# Sort by temporal metadata (latest first)
granules_sorted = sorted(
    granules,
    key=lambda g: g["umm"]["TemporalExtent"]["RangeDateTime"]["BeginningDateTime"],
    reverse=True
)

# Take the two latest granules
latest_two = granules_sorted[:2]

# Print metadata for each
for i, g in enumerate(latest_two, 1):
    umm = g["umm"]
    print(f"\n=== Granule {i} ===")
    print(f"Title: {umm.get('GranuleUR')}")
    print(f"Start Time: {umm['TemporalExtent']['RangeDateTime']['BeginningDateTime']}")
    print(f"End Time:   {umm['TemporalExtent']['RangeDateTime']['EndingDateTime']}")
    print(f"Spatial Extent: {umm.get('SpatialExtent', {})}")
    print(f"Data URLs:")
    for url_info in umm.get("RelatedUrls", []):
        if "URL" in url_info:
            print(f"  - {url_info['URL']}")

# Download both to local folder
earthaccess.download(latest_two, "./emit_data/")
