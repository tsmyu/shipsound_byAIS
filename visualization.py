import matplotlib.pyplot as plt
import os


def plot_geolocation(idx, df, record_pos, output_dir):
    """
    Plots geolocation data for vessels and saves the output as a PNG file.

    Args:
        idx (int): Index for saving the output file.
        df (DataFrame): DataFrame containing the AIS data.
        record_pos (tuple): Tuple of the recording position (longitude, latitude).
        output_dir (str): Path to the output directory where the image will be saved.
    """
    fig, ax = plt.subplots()
    colors = ["b", "g", "r", "c", "m", "y", "k"]
    unique_mmsi = df["mmsi"].unique()

    ax.scatter(record_pos[0], record_pos[1], c="b", label="rec_pos", marker="*")
    ax.text(
        record_pos[0],
        record_pos[1],
        "rec_pos",
        fontsize=10,
        ha="right",
        va="top",
    )

    handles, labels = [], []
    for i, mmsi in enumerate(unique_mmsi):
        vessel_df = df[df["mmsi"] == mmsi]
        scatter = ax.scatter(
            vessel_df["longitude"],
            vessel_df["latitude"],
            label=vessel_df["vessel_name"].iloc[0],
        )
        handles.append(scatter)
        labels.append(vessel_df["vessel_name"].iloc[0])
        vessel_df_sorted = vessel_df.sort_values("dt_pos_utc")
        ax.plot(
            vessel_df_sorted["longitude"],
            vessel_df_sorted["latitude"],
            linestyle="-",
        )

        for _, row in vessel_df.iterrows():
            ax.text(
                row["longitude"],
                row["latitude"],
                row["dt_pos_utc"].strftime("%Y-%m-%d %H:%M:%S"),
                fontsize=8,
                ha="right",
                va="top",
            )

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.legend(handles, labels, bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.savefig(os.path.join(output_dir, f"{idx}.png"), bbox_inches="tight")
