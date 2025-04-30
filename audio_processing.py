import soundfile as sf
import os
import datetime
import json
import tomli_w  # TOMLファイルの書き込み用ライブラリを追加
import pandas as pd
import numpy as np


def cut_wav_file(
    wav_file0,
    wav_file1,
    record_type,
    record_start_time,
    start_time,
    end_time,
    data_sample_num,
    output_dir,
    metadata_for_dis,
    record_pos,
    wav_durations,
    current_wav_index,
):
    data0, samplerate = sf.read(wav_file0, dtype="int16")
    data1, _ = sf.read(wav_file1, dtype="int16")
    if record_type == 2:
        data0 = data0[:, 0]
        data1 = data1[:, 0]
    data = np.concatenate([data0, data1], axis=0)

    start_sample = int((start_time - record_start_time).total_seconds() * samplerate)
    end_sample = int((end_time - record_start_time).total_seconds() * samplerate)

    if data_sample_num < start_sample and data_sample_num + len(data) > end_sample:
        print(f"cutting.....")
        cut_data = data[
            (start_sample - data_sample_num) : (end_sample - data_sample_num)
        ]
        wav_name = f"cut_{start_time.strftime('%Y%m%d_%H%M%S')}_{record_pos[0]}_{record_pos[1]}"
        cut_file = os.path.join(output_dir, wav_name + ".wav")
        sf.write(cut_file, cut_data, samplerate)

        # 使用するWAVファイルを決定
        mother_source_idx = current_wav_index
        if data_sample_num < start_sample + (end_sample - start_sample) / 2:
            mother_source = os.path.basename(wav_file0)
        else:
            mother_source = os.path.basename(wav_file1)
            mother_source_idx = current_wav_index + 1

        metadata_for_dis["source_info"]["mother_source_name"] = mother_source

        # start_dateからmother_source_nameのwavファイルが始まるまでの時間を計算
        # 元のstart_dateから母ファイルが始まるまでの経過時間を計算（前のWAVファイルの長さを累積）
        total_previous_duration_seconds = 0
        for i in range(mother_source_idx):
            total_previous_duration_seconds += wav_durations[i]

        # 母ファイルの開始時間を計算
        mother_start_time = record_start_time + datetime.timedelta(
            seconds=total_previous_duration_seconds
        )
        metadata_for_dis["source_info"]["mother_source_start_time"] = (
            mother_start_time.strftime("%Y%m%d_%H%M%S")
        )

        # 母ファイル内での切り出し開始時間を計算
        # start_sampleは記録開始からの位置、data_sample_numは現在処理中のファイルの開始位置
        # 現在のファイルの開始位置からの相対位置を計算し、それに基づいてcut_source_start_time_in_mother_sourceを設定
        cut_start_in_mother = (
            start_sample - data_sample_num
        )  # 母ファイル内のサンプル位置
        cut_seconds_in_mother = cut_start_in_mother / samplerate  # 秒数に変換

        # 秒数を時:分:秒形式に変換
        hours, remainder = divmod(cut_seconds_in_mother, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_format = f"{int(hours):02d}:{int(minutes):02d}:{seconds:.2f}"

        metadata_for_dis["source_info"][
            "cut_source_start_time_in_mother_source"
        ] = f"{cut_start_in_mother} samples ({time_format})"

        # Set the cut_source_name to match the actual cut WAV file name
        cut_wav_filename = f"cut_{start_time.strftime('%Y%m%d_%H%M%S')}.wav"
        metadata_for_dis["source_info"]["cut_source_name"] = cut_wav_filename

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
    audio_config,
):
    """
    Cuts the WAV file based on the shortest distance information and generates corresponding metadata.

    Args:
        wav_list (list): List of WAV files.
        meta_data (dict): Metadata from a TOML file.
        start_tim (str): Start time for the recording.
        distances (DataFrame): DataFrame of shortest distances between vessels and the recording position.
        distance_list (DataFrame): DataFrame of distances between the recording position and other vessels.
        output_dir (str): Path to the output directory where the files will be saved.
        record_pos (tuple): The recording position (latitude, longitude).
        audio_config (dict): Dictionary containing audio processing parameters from config.toml.
    """
    # Load parameters from config
    cut_margin_minutes = audio_config.get("cut_margin_minutes", 1)  # Default 1 minute

    record_start_time = pd.to_datetime(start_tim)
    wav_output_dir = os.path.join(output_dir, "wav")
    os.makedirs(wav_output_dir, exist_ok=True)
    record_type = meta_data["observation_info"]["record_info"]["channel_num"]

    # 各WAVファイルの継続時間（秒）を計算
    wav_durations = []
    for wav_file in wav_list:
        with sf.SoundFile(wav_file) as f:
            duration = len(f) / f.samplerate
            wav_durations.append(duration)

    for id, distance in distances.iterrows():
        metadata_for_dis = meta_data.copy()
        print(f"target distance data:{id}/{distances.shape[0]}")
        min_distance_time = distance["min_distance_time"]
        # Use cut_margin_minutes from config
        margin_delta = datetime.timedelta(minutes=cut_margin_minutes)
        start_time = min_distance_time - margin_delta
        end_time = min_distance_time + margin_delta
        data_sample_num = 0
        for idx in range(len(wav_list) - 1):
            sample_num, flag, meta_d, wav_name = cut_wav_file(
                wav_list[idx],
                wav_list[idx + 1],
                record_type,
                record_start_time,
                start_time,
                end_time,
                data_sample_num,
                wav_output_dir,
                metadata_for_dis,
                record_pos,
                wav_durations,
                idx,
            )
            if flag:
                # Set the vessel sound source information
                # Category for vessel sounds is Anthrophony (1)
                meta_d["source_info"]["category"] = 1

                # Set the vessel name as the sound source using the format: vessel_type(vessel_name)
                vessel_type = (
                    distance["vessel_type"]
                    if not pd.isna(distance["vessel_type"])
                    else "Unknown"
                )
                vessel_name = (
                    distance["vessel_name"]
                    if not pd.isna(distance["vessel_name"])
                    else "Unknown"
                )
                meta_d["source_info"]["sound_source"] = f"{vessel_type}({vessel_name})"

                # Reliability is 2 since we confirmed the vessel via AIS data
                meta_d["source_info"]["reliability"] = 2

                # Set environmental conditions
                # These would typically be measured or known, but for now we'll set defaults
                meta_d["source_info"]["precipitation"] = 0.0
                meta_d["source_info"]["wind_speed"] = 0.0

                # Add condition information
                meta_d["source_info"][
                    "condition"
                ] = f"Ship distance: {distance['min_distance [m]']:.2f}m"

                # Get ship length and width from AIS data if available
                ship_length = (
                    distance["length"]
                    if "length" in distance.index and not pd.isna(distance["length"])
                    else "Unknown"
                )
                ship_width = (
                    distance["width"]
                    if "width" in distance.index and not pd.isna(distance["width"])
                    else "Unknown"
                )

                # Format vessel details for the appendix field including length and width
                vessel_info_str = (
                    f"mmsi: {distance['mmsi']}, "
                    f"vessel_type: {vessel_type}, "
                    f"length: {ship_length}, "
                    f"width: {ship_width}, "
                    f"min_distance_m: {distance['min_distance [m]']}, "
                    f"min_distance_time: {distance['min_distance_time'].strftime('%Y-%m-%dT%H:%M:%S')}"
                )

                # Set appendix with vessel information
                meta_d["source_info"]["appendix"] = vessel_info_str

                # TOMLファイルを生成して保存
                with open(f"{wav_output_dir}/{wav_name}.toml", "wb") as f:
                    tomli_w.dump(meta_d, f)
                break

            else:
                data_sample_num += sample_num
