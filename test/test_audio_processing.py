import os
import sys
import unittest
import pandas as pd
import numpy as np
import soundfile as sf
import shutil
import datetime
import tomli

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from audio_processing import cut_wav_file, cut_wav_and_make_metadata


class TestAudioProcessing(unittest.TestCase):
    def setUp(self):
        # テスト用ディレクトリを作成
        self.test_dir = os.path.join(os.path.dirname(__file__), "test_output")
        os.makedirs(self.test_dir, exist_ok=True)

        # テスト用のWAVファイルを作成
        self.sample_rate = 44100
        self.create_test_wav_files()

        # テスト用のメタデータを作成
        self.metadata = {
            "observation_info": {
                "date_info": {
                    "time_zone": "JST",
                    "start_date": "2024-03-19T06:53:00",
                },
                "location_info": {
                    "position": [32.71161, 129.77558],
                    "installation_depth": 100.0,
                },
                "record_info": {
                    "channel_num": 1,
                },
            },
            "source_info": {
                "category": 1,
                "reliability": 2,
                "cut_source_name": "",
                "mother_source_name": "",
                "mother_source_start_time": "",
                "cut_source_start_time_in_mother_source": "",
            },
        }

        # テスト用の距離データを作成（録音開始12分後に対応）
        start_time = pd.to_datetime("2024-03-19 06:53:00")
        target_time = start_time + datetime.timedelta(seconds=120)  # 開始から2分後
        self.distances = pd.DataFrame(
            {
                "mmsi": [123456789],
                "vessel_name": ["Test Vessel"],
                "vessel_type": ["Cargo"],
                "length": [100],
                "width": [20],
                "min_distance [m]": [500.0],
                "min_distance_pos": [[32.7, 129.7]],
                "min_distance_time": [target_time],
            }
        )

    def tearDown(self):
        # テスト後にディレクトリを削除
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def create_test_wav_files(self):
        # テスト用WAVファイルを作成（各60秒）- より長い時間を設定
        self.wav_files = []
        for i in range(3):
            # 60秒のサイン波（440Hz）
            duration = 60
            t = np.linspace(0, duration, int(self.sample_rate * duration), False)
            data = np.sin(2 * np.pi * 440 * t) * 0.5
            data = (data * 32767).astype(np.int16)

            file_path = os.path.join(self.test_dir, f"test_{i}.wav")
            sf.write(file_path, data, self.sample_rate)
            self.wav_files.append(file_path)

    def test_cut_wav_file(self):
        # テスト用のパラメータ - 条件を確実に満たすよう設定
        record_start_time = pd.to_datetime("2024-03-19 06:53:00")
        # cut_wav_file関数の条件を満たすように時間設定
        # 開始から15秒後に切り出し開始（第1ファイルに含まれる）
        start_time = record_start_time + datetime.timedelta(seconds=15)
        end_time = start_time + datetime.timedelta(seconds=5)
        data_sample_num = 0
        wav_durations = [60, 60, 60]  # 各WAVファイルは60秒

        # 関数を実行
        length, flag, metadata, wav_name = cut_wav_file(
            self.wav_files[0],
            self.wav_files[1],
            1,
            record_start_time,
            start_time,
            end_time,
            data_sample_num,
            self.test_dir,
            self.metadata.copy(),
            [32.71161, 129.77558],
            wav_durations,
            0,
        )

        # 結果を検証
        self.assertTrue(flag, "切り出しが正常に行われませんでした")
        self.assertIsNotNone(wav_name, "生成されたWAV名がNoneです")

        # mother_source_nameの検証
        self.assertEqual(metadata["source_info"]["mother_source_name"], "test_0.wav")

        # mother_source_start_timeの検証 (第1ファイルなので開始時間はrecord_start_time)
        expected_mother_start_time = record_start_time.strftime("%Y%m%d_%H%M%S")
        self.assertEqual(
            metadata["source_info"]["mother_source_start_time"],
            expected_mother_start_time,
        )

        # cut_source_start_time_in_mother_sourceの検証 (15秒後なので15*44100サンプル)
        expected_samples = 15 * self.sample_rate
        self.assertIn(
            str(expected_samples),
            metadata["source_info"]["cut_source_start_time_in_mother_source"],
        )
        # 新しい時間形式で検証 (00:00:15.00)
        self.assertIn(
            "00:00:15.00",
            metadata["source_info"]["cut_source_start_time_in_mother_source"],
        )

    def test_cut_wav_and_make_metadata_isolated(self):
        """cut_wav_and_make_metadata関数の一部のみをテスト"""
        # テスト記録時間を設定
        record_start_time = pd.to_datetime("2024-03-19 06:53:00")

        # テスト用の簡易的なcut_wav_file関数を作成
        original_cut_wav_file = cut_wav_file

        try:
            # モック関数をテスト
            def mock_cut_wav_file(*args, **kwargs):
                metadata_for_dis = args[8].copy()  # metadata_for_disを取得
                # テスト用の設定を追加
                metadata_for_dis["source_info"]["mother_source_name"] = "test_0.wav"
                metadata_for_dis["source_info"]["mother_source_start_time"] = (
                    record_start_time.strftime("%Y%m%d_%H%M%S")
                )
                # 長めの時間（2時間5分15秒）をテスト
                metadata_for_dis["source_info"][
                    "cut_source_start_time_in_mother_source"
                ] = "661500 samples (02:05:15.00)"

                wav_name = f"cut_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{args[9][0]}_{args[9][1]}"
                return len(args[0]), True, metadata_for_dis, wav_name

            # 一時的に関数を置き換え
            import audio_processing

            audio_processing.cut_wav_file = mock_cut_wav_file

            # テスト実行
            cut_wav_and_make_metadata(
                self.wav_files,
                self.metadata.copy(),
                record_start_time,
                self.distances,
                pd.DataFrame(),
                self.test_dir,
                [32.71161, 129.77558],
            )

            # TOMLファイルが生成されているか確認
            wav_output_dir = os.path.join(self.test_dir, "wav")
            toml_files = [f for f in os.listdir(wav_output_dir) if f.endswith(".toml")]
            self.assertEqual(len(toml_files), 1, "TOMLファイルが生成されていません")

            # TOMLファイルの内容を検証
            toml_path = os.path.join(wav_output_dir, toml_files[0])
            with open(toml_path, "rb") as f:
                toml_data = tomli.load(f)

            # デバッグ用に内容を表示
            print("\nTOML file content:")
            print(
                f"cut_source_start_time_in_mother_source: {toml_data['source_info']['cut_source_start_time_in_mother_source']}"
            )

            # mother_source_start_timeとcut_source_start_time_in_mother_sourceが存在するか確認
            self.assertIn("mother_source_start_time", toml_data["source_info"])
            self.assertIn(
                "cut_source_start_time_in_mother_source", toml_data["source_info"]
            )

            # 母ファイルの位置と切り出し位置が正しいか確認
            self.assertEqual(
                toml_data["source_info"]["mother_source_name"], "test_0.wav"
            )
            self.assertIn(
                "samples",
                toml_data["source_info"]["cut_source_start_time_in_mother_source"],
            )
            # 秒表記ではなく時間表記を確認
            self.assertIn(
                "02:05:",
                toml_data["source_info"]["cut_source_start_time_in_mother_source"],
            )

        finally:
            # 元の関数に戻す
            audio_processing.cut_wav_file = original_cut_wav_file


if __name__ == "__main__":
    unittest.main()
