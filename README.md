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
│   ├── test_visualization.py
│   └── run_tests.py          # Script to run all tests
├── results/                  # Default output directory for CSV files and plots (ignored by git)
├── spectrograms/             # Default output directory for spectrogram images (ignored by git)
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
Contains functions to cut WAV audio files based on calculated time ranges (derived from vessel proximity) and generate corresponding metadata appendix files.

### `main.py`
The main script that integrates all modules. It reads the configuration from `config.toml`, executes the pipeline (reading data, calculating distances, optionally creating visualizations and cutting WAV files based on the config), and saves the results.

### `config.toml`
A configuration file using the TOML format to set parameters for various processing steps, such as file paths, calculation thresholds, plot settings, and output flags (e.g., whether to generate figures or cut audio). This allows easy modification of the project's behavior without changing the code.

## Requirements

1.  **Python:** (Specify version if applicable, e.g., Python 3.8+ recommended)
2.  **Dependencies:** Install the necessary libraries using `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configuration File:** A `config.toml` file must be present in the project root directory. You can copy and modify the provided template or create your own based on the required parameters. See `config.toml.template` (if provided) or the parameter usage within the scripts for details.

## Usage

To execute the pipeline, run the `main.py` script, providing the path to the configuration file:

```bash
python main.py --config_path <path_to_your_config.toml>
```

### Arguments

- `-c`, `--config_path`: Path to the configuration TOML file. This file dictates input paths, output behavior (figure generation, audio cutting, CSV output), and various processing parameters.

All other operational parameters (like AIS paths, WAV paths, time settings, output flags `fig_flag`, `csv_flag`, etc.) should be set within the `config.toml` file.

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
