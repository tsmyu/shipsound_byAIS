# AIS and WAV Processing Project

This project is designed to process AIS (Automatic Identification System) data, WAV audio files, and associated metadata to analyze vessel trajectories, calculate distances, cut relevant audio segments, and generate visualizations like geolocation plots and time-averaged spectrograms. The project is modular, with functionalities separated across multiple files and configured via a central TOML file.

## Project Structure

```bash
.
├── audio_processing.py       # Handles WAV file cutting based on timestamps
├── data_processing.py        # Functions for reading and processing AIS data
├── distance_calculation.py   # Functions for calculating vessel distances
├── visualization.py          # Plotting geolocation and time-averaged spectrograms
├── main.py                   # Main execution script coordinating the workflow
├── config.toml               # Configuration file for parameters and flags
├── requirements.txt          # Dependencies required for the project
├── test/                     # Directory containing unit tests
├── Cases_of_caution.md       # Notes on development practices and optimization
├── .gitignore                # Specifies intentionally untracked files for Git
└── README.md                 # Project documentation (this file)
```

## Modules Overview

### `data_processing.py`
Contains functions for reading and processing AIS data, converting timestamps, and complementing vessel trajectories with interpolated data.

### `distance_calculation.py`
Contains functions to calculate the shortest distance between vessels and the recording position, using the Haversine formula.

### `visualization.py`
Includes functions for generating visualizations:
- **Geolocation Plots:** Show vessel trajectories relative to the recording point.
- **Time-Averaged Spectrograms:** Display the frequency content of the mother source WAV file over its entire duration. For long files, the spectrogram represents time-averaged power spectral density to manage memory usage. Vertical lines indicate the calculated cut sections for nearby vessels.

### `audio_processing.py`
Contains functions to cut WAV audio files based on calculated time ranges (derived from vessel proximity) and generate corresponding metadata appendix files. The cutting process considers multiple conditions:

1. **Time Range Selection:** The time range for each cut is centered around the time of minimum distance between the vessel and recording position.
2. **Distance Threshold:** Only vessels that come within a configurable maximum distance (`max_cut_distance` in config.toml) are considered for cutting.
3. **Isolation Condition:** A vessel segment is only cut when, at its time of minimum distance, it is the closest vessel to the recording position (compared to all other vessels).
4. **Margin Configuration:** The time margin before and after the minimum distance point is configurable (`cut_margin_minutes` in config.toml).

The cut WAV files are stored with metadata about the vessel, including MMSI, vessel type, vessel name, minimum distance, and timestamps.

### `main.py`
The main script that integrates all modules. It reads the configuration from `config.toml`, executes the pipeline (reading data, calculating distances, optionally creating visualizations and cutting WAV files based on the config), and saves the results.

### `config.toml`
A configuration file using the TOML format to set parameters for various processing steps, such as file paths, calculation thresholds, plot settings, and output flags (e.g., whether to generate figures or cut audio). This allows easy modification of the project's behavior without changing the code.

Key audio processing parameters include:
- `cut_margin_minutes`: The time margin (in minutes) before and after the point of minimum distance for WAV cutting
- `max_cut_distance`: Maximum distance threshold (in meters) for vessel consideration
- `check_other_vessels`: Whether to check if a vessel is the closest at its minimum distance time

## Requirements

1.  **Python:** (Specify version if applicable, e.g., Python 3.8+ recommended)
2.  **Dependencies:** Install the necessary libraries using `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configuration File:** A `config.toml` file must be present in the project root directory. You can copy and modify the provided template or create your own based on the required parameters. See `config.toml.template` (if provided) or the parameter usage within the scripts for details.

## Usage

To execute the pipeline, run the `main.py` script, providing the necessary command-line arguments:

```bash
python main.py -a AIS_PATH -w WAV_PATH -m TOML_PATH -t RECORD_START_TIME [-c CONFIG_PATH] [-ff] [-mf] [-cf]
```

### Command-line Arguments

The script accepts the following arguments:

- `-a`, `--ais_path` (required): Path to the folder containing AIS data CSV files.
- `-w`, `--wav_path` (required): Path to the folder containing WAV audio files.
- `-m`, `--toml_path` (required): Path to the TOML metadata file with observation information.
- `-t`, `--record_start_time` (required): Record start time in ISO format (e.g., '2024-03-19T06:53:00').
- `-c`, `--config_path` (optional): Path to the configuration TOML file. Defaults to 'config.toml'.
- `-ff`, `--fig_flag` (flag): Generate visualization figures (geolocation plots and spectrograms).
- `-mf`, `--movie_flag` (flag): Generate movies (not currently implemented).
- `-cf`, `--csv_flag` (flag): Save distance calculation results as CSV files.

Example:
```bash
python main.py -a ./data/ais -w ./data/wav -m ./metadata.toml -t 2024-03-19T06:53:00 -c ./config.toml -ff -cf
```

### Configuration File

The `config.toml` file contains several sections for different aspects of the processing pipeline:

#### General Settings

```toml
[general]
# This section can contain general settings
```

#### Audio Processing Parameters

```toml
[audio_processing]
# Time margin in minutes before and after minimum distance time
cut_margin_minutes = 5

# Maximum distance threshold (meters) for WAV cutting
# Vessels farther than this distance will be skipped
max_cut_distance = 10000.0

# Enable checking if vessel is the closest at its minimum distance time
# When true, a vessel will only be cut if it's the closest vessel at its minimum distance time
check_other_vessels = true
```

#### Visualization Settings

```toml
[visualization]
# Parameters for time-averaged spectrograms
chunk_duration_seconds = 300  # Duration of chunks for processing
spectrogram_nperseg = 1024    # Segment length for STFT

# Plotting appearance
plot_max_freq_bins = 200      # Maximum frequency bins to display
plot_db_min = -80             # Minimum dB level for colormap
plot_db_max = -10             # Maximum dB level for colormap
plot_max_cuts = 15            # Maximum number of cut annotations to display
plot_dpi = 150                # DPI for saving images
```

### Common Use Cases

#### Generate Only Visualizations

To generate only visualizations without cutting WAV files:

```bash
python main.py -a ./data/ais -w ./data/wav -m ./metadata.toml -t 2024-03-19T06:53:00 -ff
```

#### Process and Save Results as CSV

To process the data and save the distance calculation results without visualizations:

```bash
python main.py -a ./data/ais -w ./data/wav -m ./metadata.toml -t 2024-03-19T06:53:00 -cf
```

#### Full Processing with Custom Configuration

To run the full pipeline with all features enabled using a custom configuration file:

```bash
python main.py -a ./data/ais -w ./data/wav -m ./metadata.toml -t 2024-03-19T06:53:00 -c ./custom_config.toml -ff -cf
```

## Visualization Features

### Vessel Trajectory Plots
If enabled in `config.toml` (`fig_flag = true`), the program generates plots showing vessel trajectories and their positions relative to the recording position. Saved typically in the `results/` directory.

### Spectrograms with Cut Indicators
If enabled in `config.toml` (`fig_flag = true`), the program generates spectrograms for each mother source WAV file. These are saved in the `spectrograms/` subfolder within the output directory specified in the config. Each spectrogram includes:

- **Full Audio Visualization:** Displays the frequency content over the entire duration of the mother source file. For long files (> memory/processing limits), this is a **time-averaged spectrogram**, showing the average power spectrum over configured time chunks (e.g., 10 minutes).
- **Cut Indicators:** Vertical dashed lines showing the calculated start and end times for audio cuts corresponding to nearby vessels.
- **Labels:** Information about the vessel associated with each cut (e.g., name, MMSI, minimum distance) is displayed near the corresponding lines.
- **Color Coding:** Different colors may be used to distinguish cuts for different vessels.

This visualization helps understand which time segments in the original audio correspond to specific vessel passages, even for very long recordings.

## Tests

Automated tests are included to verify the functionality of different modules.

To run all tests, execute the `run_tests.py` script from the project's root directory:

```bash
python -m unittest discover -s test
```
or simply:
```bash
python test/run_tests.py
```

To run a specific test file (e.g., `test_visualization.py`):

```bash
python -m unittest test.test_visualization
```

When adding new features or fixing bugs, please add corresponding tests in the `test/` directory (using filenames starting with `test_`) and ensure all tests pass.

## Development Notes

For guidelines on development practices, coding style, and notes on optimization efforts (especially regarding performance and memory usage), please refer to the `Cases_of_caution.md` file.
