# AIS and WAV Processing Project

This project is designed to process AIS (Automatic Identification System) data, WAV audio files, and metadata files to analyze vessel trajectories, calculate distances, and generate visualizations. The project is modular, with functionalities separated across multiple files for better maintainability and readability.

## Project Structure

```bash
.
├── audio_processing.py       # Handles WAV file cutting and metadata generation
├── data_processing.py        # Functions for reading and processing AIS data
├── distance_calculation.py   # Functions for calculating vessel distances
├── visualization.py          # Plotting and animation of vessel trajectories
├── main.py                   # Main execution script for coordinating the workflow
├── requirements.txt          # Dependencies required for the project
└── README.md                 # Project documentation (this file)
```

## Modules Overview

### data_processing.py

Contains functions for reading and processing AIS data, converting timestamps, and complementing vessel trajectories with interpolated data.

### distance_calculation.py

Contains functions to calculate the shortest distance between vessels and the recording position, using the Haversine formula for distance calculations.

### visualization.py

Includes functions for generating visualizations such as geolocation plots and spectrograms of WAV files with cut section indicators. The spectrogram visualization shows vertical lines indicating where audio segments have been cut from the mother source files, along with vessel information.

### audio_processing.py

Contains functions to cut WAV audio files based on specific time ranges and to generate corresponding metadata.

### main.py

The main script that integrates all modules, executing the full pipeline: reading AIS and WAV data, calculating distances, creating visualizations, and cutting WAV files.

## Requirements

Install the necessary dependencies using the provided `requirements.txt` file. Run the following command in your terminal:

```bash
pip install -r requirements.txt
```

## Usage

To execute the pipeline, run the `main.py` script with the necessary arguments:

```python
python main.py --ais_path <path_to_ais_data> --wav_path <path_to_wav_data> --toml_path <path_to_toml_metadata> --record_start_time <start_time> --fig_flag <True|False> --movie_flag <True|False> --csv_flag <True|False>
```

## Arguments

- `-a`, `--ais_path`: Path to the folder containing AIS data CSV files.
- `-w`, `--wav_path`: Path to the folder containing WAV audio files.
- `-m`, `--toml_path`: Path to the metadata TOML file.
- `-t`, `--record_start_time`: Record start time in ISO format (default: "2024-03-19T06:53:00").
- `-ff`, `--fig_flag`: Set to True if you want to generate vessel trajectory plots and spectrograms with cut sections (default: False).
- `-mf`, `--movie_flag`: Set to True if you want to create an animation of vessel trajectories (default: False).
- `-cf`, `--csv_flag`: Set to True if you want to output CSV files with calculated distances (default: False).

## Visualization Features

### Vessel Trajectory Plots
When `--fig_flag` is set to True, the program will generate plots showing vessel trajectories and their positions relative to the recording position.

### Spectrograms with Cut Indicators
When `--fig_flag` is set to True, the program will also generate spectrograms for each mother source WAV file with vertical lines indicating the locations where audio has been cut. These spectrograms are saved in a "spectrograms" subfolder within the output directory. Each spectrogram includes:

- Full audio visualization of the mother source file
- Vertical dashed lines showing the cut start and end positions
- Labels with vessel information (name, MMSI, and distance)
- Different colors for different vessel cuts

This visualization helps to understand which parts of the original audio files were used for each vessel and how the cuts relate to the audio content.

## テスト

本プロジェクトには自動化されたテストが含まれています。テストを実行するには、以下の手順に従ってください：

```bash
# プロジェクトのルートディレクトリから実行
python -m test.run_tests
```

または個別のテストファイルを実行する場合：

```bash
# test ディレクトリから実行
cd test
python test_audio_processing.py
```

テストを追加する場合は、`test`ディレクトリ内に`test_`で始まるファイル名で作成してください。
新しい機能を実装した場合は、必ず対応するテストを作成し、実行して機能の正確性を検証してください。
