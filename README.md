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

# Modules Overview

## `data_processing.py`
Contains functions for reading and processing AIS data, converting timestamps, and complementing vessel trajectories with interpolated data.

## `distance_calculation.py`
Contains functions to calculate the shortest distance between vessels and the recording position, using the Haversine formula for distance calculations.

## `visualization.py`
Includes functions for generating visualizations such as geolocation plots and animations of vessel trajectories over time.

## `audio_processing.py`
Contains functions to cut WAV audio files based on specific time ranges and to generate corresponding metadata.

## `main.py`
The main script that integrates all modules, executing the full pipeline: reading AIS and WAV data, calculating distances, creating visualizations, and cutting WAV files.

# Requirements

Install the necessary dependencies using the provided `requirements.txt` file. Run the following command in your terminal:

```bash
pip install -r requirements.txt

# Usage

To execute the pipeline, run the `main.py` script with the necessary arguments:

```bash
python main.py --ais_path <path_to_ais_data> --wav_path <path_to_wav_data> --json_path <path_to_json_metadata> --fig_flag <True|False> --movie_flag <True|False> --csv_flag <True|False>

Arguments
--ais_path: Path to the folder containing AIS data CSV files.
--wav_path: Path to the folder containing WAV audio files.
--json_path: Path to the metadata JSON file.
--fig_flag: Set to True if you want to generate vessel trajectory plots. Under constraction.
--movie_flag: Set to True if you want to create an animation of vessel trajectories. Under constraction.
--csv_flag: Set to True if you want to output CSV files with calculated distances.
