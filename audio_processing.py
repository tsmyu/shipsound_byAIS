import soundfile as sf
import os
import datetime
import json
import pandas as pd
import numpy as np


def cut_wav_file(
    wav_file0,
    wav_file1,
    record_type,
    wav_start_time,
    start_time,
    end_time,
    data_sample_num,
    output_dir,
    metadata_for_dis,
    record_pos,
):
    data0, samplerate = sf.read(wav_file0, dtype="int16")
    data1, _ = sf.read(wav_file1, dtype="int16")
    if record_type == 2:
        data0 = data0[:, 0]
        data1 = data1[:, 0]
    data = np.concatenate([data0, data1], axis=0)

    start_sample = int(
        (start_time - wav_start_time).total_seconds() * samplerate
    )
    end_sample = int((end_time - wav_start_time).total_seconds() * samplerate)

    if (
        data_sample_num < start_sample
        and data_sample_num + len(data) > end_sample
    ):
        print(f"cutting.....")
        cut_data = data[
            (start_sample - data_sample_num) : (end_sample - data_sample_num)
        ]
        wav_name = f"cut_{start_time.strftime('%Y%m%d_%H%M%S')}_{record_pos[0]}_{record_pos[1]}"
        cut_file = os.path.join(output_dir, wav_name + ".wav")
        sf.write(cut_file, cut_data, samplerate)
        if data_sample_num < start_sample + (end_sample - start_sample) / 2:
            metadata_for_dis["source_info"]["mother_source_name"] = (
                os.path.basename(wav_file0)
            )
        else:
            metadata_for_dis["source_info"]["mother_source_name"] = (
                os.path.basename(wav_file1)
            )
        metadata_for_dis["source_info"]["mother_source_start_time"] = (
            wav_start_time.strftime("%Y%m%d_%H%M%S")
        )
        metadata_for_dis["source_info"][
            "cut_source_name"
        ] = f"cut_{start_time.strftime('%Y%m%d_%H%M%S')}.wav"
        metadata_for_dis["source_info"][
            "cut_source_start_time_in_mother_source"
        ] = f"{(start_time - wav_start_time)}"

        return len(data0), True, metadata_for_dis, wav_name
    else:
        print(f"out of target range. next wav.....")
        return len(data0), False, metadata_for_dis, None


def cut_wav_and_make_metadata(
    wav_list,
    meta_data,
    start_tim,
    distances,
    distance_list,
    output_dir,
    record_pos,
):
    """
    Cuts the WAV file based on the shortest distance information and generates corresponding metadata.

    Args:
        wav_list (list): List of WAV files.
        meta_data (dict): Metadata from a JSON file.
        start_tim (str): Start time for the recording.
        distances (DataFrame): DataFrame of shortest distances between vessels and the recording position.
        distance_list (DataFrame): DataFrame of distances between the recording position and other vessels.
        output_dir (str): Path to the output directory where the files will be saved.
        record_pos (tuple): The recording position (latitude, longitude).
    """
    wav_start_time = pd.to_datetime(start_tim)
    wav_output_dir = os.path.join(output_dir, "wav")
    os.makedirs(wav_output_dir, exist_ok=True)
    record_type = meta_data["observation_info"]["record_info"]["channel_num"]

    for id, distance in distances.iterrows():
        metadata_for_dis = meta_data.copy()
        print(f"target distance data:{id}/{distances.shape[0]}")
        min_distance_time = distance["min_distance_time"]
        start_time = min_distance_time - datetime.timedelta(minutes=1)
        end_time = min_distance_time + datetime.timedelta(minutes=1)
        data_sample_num = 0
        for idx in range(len(wav_list) - 1):
            sample_num, flag, meta_d, wav_name = cut_wav_file(
                wav_list[idx],
                wav_list[idx + 1],
                record_type,
                wav_start_time,
                start_time,
                end_time,
                data_sample_num,
                wav_output_dir,
                metadata_for_dis,
                record_pos,
            )
            if flag:
                meta_d["source_info"]["category15"] = distance["vessel_type"]
                meta_d["source_info"]["category6"] = distance["vessel_type"]
                meta_d["source_info"]["reliability"] = "By AIS"
                meta_d["source_info"]["sound_source"] = distance["vessel_name"]
                meta_d["source_info"]["apendix"] = None
                meta_d["source_info"]["comment"] = None
                with open(f"{wav_output_dir}/{wav_name}.json", "w") as f:
                    json.dump(meta_d, f)
                break

            else:
                data_sample_num += sample_num
