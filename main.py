import os
import argparse
from natsort import natsorted
import glob
import json
import pandas as pd
from data_processing import read_ais, complement_trajectory
from distance_calculation import calculate_shortest_distance, haversine
from visualization import plot_geolocation
from audio_processing import cut_wav_and_make_metadata


def read_json_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


def main(ais_path, wav_path, json_path, flag_fig, flag_movie, flag_csv):
    ais_list = natsorted(glob.glob(f"{ais_path}/*.csv"))
    wav_list = natsorted(glob.glob(f"{wav_path}/*.WAV"))
    meta_data = read_json_file(json_path)
    start_tim = pd.to_datetime(
        f"{meta_data['observation_info']['date_info']['start_date']} {meta_data['observation_info']['date_info']['start_time']}"
    )
    record_pos = eval(
        meta_data["observation_info"]["location_info"]["position"]
    )
    record_depth = meta_data["observation_info"]["location_info"][
        "installation_depth"
    ]

    for idx, ais_data in enumerate(ais_list):
        print(
            f"Processing AIS data: {idx}/{len(ais_list)}, {os.path.basename(ais_data)}"
        )
        output_dir = os.path.join(
            os.path.dirname(ais_data),
            os.path.splitext(os.path.basename(ais_data))[0],
        )
        os.makedirs(output_dir, exist_ok=True)

        ais_df = read_ais(ais_data)
        if flag_fig:
            plot_geolocation(idx, ais_df, record_pos, output_dir)

        comp_df = complement_trajectory(ais_data)
        distances = calculate_shortest_distance(
            comp_df, record_pos, record_depth
        )
        distances_df = pd.DataFrame(distances)

        if flag_csv:
            distances_df.to_csv(
                os.path.join(output_dir, f"distances_{idx}.csv"), index=False
            )

        cut_wav_and_make_metadata(
            wav_list,
            meta_data,
            start_tim,
            distances_df,
            pd.DataFrame(),  # You can handle the distance list as needed.
            output_dir,
            record_pos,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ais_path", type=str, help="Path to the AIS folder.")
    parser.add_argument("--wav_path", type=str, help="Path to the WAV folder.")
    parser.add_argument(
        "--json_path", type=str, help="Path to the JSON metadata file."
    )
    parser.add_argument(
        "--fig_flag", type=bool, help="Flag for making figures.", default=False
    )
    parser.add_argument(
        "--movie_flag", type=bool, help="Flag for making movies.", default=False
    )
    parser.add_argument(
        "--csv_flag",
        type=bool,
        help="Flag for making CSV files.",
        default=False,
    )
    args = parser.parse_args()

    main(
        args.ais_path,
        args.wav_path,
        args.json_path,
        args.fig_flag,
        args.movie_flag,
        args.csv_flag,
    )
