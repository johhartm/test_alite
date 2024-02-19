import atlite
import logging
import geopandas as gpd
import pandas as pd
import glob
import matplotlib.pyplot as plt
import numpy
import rasterio
import rasterio.sample
import rasterio.vrt

import seaborn as sns

if __name__ == "__main__":
    sns.set_style("whitegrid")

    logging.basicConfig(level=logging.INFO)

    cutout = atlite.Cutout(
        path="hyrasia_project_map_long_timeframe.nc",
        module="era5",
        x=slice(50.766,55.245),
        y=slice(42.12, 50.61),
        time=slice("1990-01-01","2023-12-31"),
    )
    cutout.prepare()

    #load initial locations of wind turbines
    location_coords = gpd.read_file("data/HY1_DWG_18x100_wind_turbines_for_time_series_4326_20220324.geojson")
    #check csr of cutout and adapt coordinates of wind turbines
    #crs is the same


    # build list of installed capacities for every profile
    profiles = {}
    sites_names = location_coords.NAME.unique()
    for name in sites_names:
        subset = location_coords[location_coords["NAME"]== name]
        x = subset.centroid.x
        y = subset.centroid.y
        Capacity = 5000
        layout_df = pd.DataFrame.from_records((x, y)).T
        layout_df["Capacity"] = 5000
        layout_df.columns=("x", "y", "Capacity")
        layout = cutout.layout_from_capacity_list(layout_df)
        profiles[name] = cutout.wind(
            turbine="sgre_SG145_5MW_onshore",
            layout=layout,
            show_progress=True,
            add_cutout_windspeed=True
        )

    #load original profiles
    prof_locs = glob.glob(('data/*.csv'))
    orig_profiles = {}
    idx = pd.date_range("2021-01-01", "2021-01-31", freq="h")

    for site_name in sites_names:
        profile_file = prof_locs[[index for index, prof_loc in enumerate(prof_locs) if site_name in prof_loc][0]]
        prof = pd.read_csv(profile_file)
        prof.index = pd.to_datetime(prof.Timestamp.values)
        prof = prof.shift(-3)
        prof = prof[site_name]
        prof = prof.loc[idx]
        orig_profiles[site_name] = prof





    # plot original profiles against Atlite Profile
    for site_name in sites_names:
        compare = pd.DataFrame(
            {
                "atlite": (profiles[site_name].squeeze().to_series()/500000)*0.95,
                "DWG": orig_profiles[site_name]
            }
        )
        compare.plot(figsize=(10, 6))
        plt.ylabel("Feed-in [%]")
        plt.title("Wind time-series Project Area Jan 2021")
        plt.tight_layout()
        plt.savefig(fname = f"Plots/Diff_{site_name}.png")

# calculate statistical differences like RMSE