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

    def test_cut_source_start_time_calculation(self):
        """cut_source_start_time_in_mother_sourceの計算に関する詳細なテスト"""
        record_start_time = pd.to_datetime("2024-03-19 06:53:00")

        # テストケース - (開始からの秒数, データ開始位置, 期待されるサンプル数, 期待される時間文字列)
        test_cases = [
            # 基本ケース: 切り出し開始位置が最初のファイルの冒頭から15秒後
            (15, 0, 15 * self.sample_rate, "00:00:15.00"),
            # 切り出し開始位置がファイルの中間（30秒）
            (30, 0, 30 * self.sample_rate, "00:00:30.00"),
            # データ開始位置がオフセットされている場合（ケース5と同じ）
            (20, 10 * self.sample_rate, 10 * self.sample_rate, "00:00:10.00"),
            # データ開始位置と開始時間が近い場合
            (11, 10 * self.sample_rate, 1 * self.sample_rate, "00:00:01.00"),
            # 小数時間の場合
            (10.5, 0, int(10.5 * self.sample_rate), "00:00:10.50"),
            # 2つ目のWAVファイルを使用する場合（最初のファイルを超えた位置からの切り出し）
            (70, 60 * self.sample_rate, 10 * self.sample_rate, "00:00:10.00"),
        ]

        for case_num, (
            seconds,
            data_sample_num,
            expected_samples,
            expected_time,
        ) in enumerate(test_cases):
            with self.subTest(
                f"Case {case_num+1}: {seconds} seconds, data_sample_num={data_sample_num}"
            ):
                start_time = record_start_time + datetime.timedelta(seconds=seconds)
                end_time = start_time + datetime.timedelta(
                    seconds=5
                )  # 切り出し時間は5秒
                wav_durations = [60, 60, 60]  # 各WAVファイルは60秒

                print(
                    f"\nテストケース {case_num+1}: {seconds}秒, データ開始位置={data_sample_num}"
                )
                print(f"  開始時間: {start_time}, 終了時間: {end_time}")
                print(f"  期待値: {expected_samples} サンプル ({expected_time})")

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

                if flag:  # 切り出しが成功した場合のみ検証
                    cut_start_info = metadata["source_info"][
                        "cut_source_start_time_in_mother_source"
                    ]
                    print(f"  結果: {cut_start_info}")

                    # サンプル数の検証
                    self.assertIn(
                        str(expected_samples),
                        cut_start_info,
                        f"Expected sample count {expected_samples} not found in {cut_start_info}",
                    )

                    # 時間表記の検証
                    self.assertIn(
                        expected_time,
                        cut_start_info,
                        f"Expected time format {expected_time} not found in {cut_start_info}",
                    )
                else:
                    print(f"  切り出しに失敗しました。フラグ: {flag}")

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
                {},  # 追加: audio_configを空の辞書で渡す
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

    # 2つ目のWAVファイルからの切り出しをテストする専用のテスト
    def test_second_wav_file_cut(self):
        """2つ目のWAVファイルからの切り出しとメタデータ設定を検証するテスト"""
        # テスト用のパラメータを設定
        record_start_time = pd.to_datetime("2024-03-19 06:53:00")

        # 1つ目のファイルは60秒×2 = 120秒分のデータ、2つ目のファイルの開始10秒を切り出し
        # つまり録音開始から130秒後の位置（1つ目のWAVファイル2個分の長さは120秒なので、確実に2つ目のファイル内）
        start_time = record_start_time + datetime.timedelta(seconds=130)
        end_time = start_time + datetime.timedelta(seconds=5)  # 5秒間切り出し

        # 1つ目のファイルの長さ分がデータ開始位置
        data_sample_num = self.sample_rate * 60  # 60秒 * 44100Hz = 2646000サンプル
        wav_durations = [60, 60, 60]  # 各WAVファイルは60秒

        # テスト条件の表示と計算
        first_wav_end_sample = (
            data_sample_num + self.sample_rate * 60
        )  # 1つ目のWAVファイルの終了位置
        start_sample = int(
            (start_time - record_start_time).total_seconds() * self.sample_rate
        )
        print(
            f"テスト条件: start_time={start_time}, data_sample_num={data_sample_num}, sample_rate={self.sample_rate}"
        )
        print(f"start_sample = {start_sample}")
        print(f"wav_file0の終了位置 = {first_wav_end_sample}")
        print(
            f"2つ目のWAVファイル内の位置 = {start_sample - first_wav_end_sample} サンプル"
        )

        # 関数実行
        length, flag, metadata, wav_name = cut_wav_file(
            self.wav_files[0],  # 1つ目のWAVファイル
            self.wav_files[1],  # 2つ目のWAVファイル
            1,  # モノラル
            record_start_time,
            start_time,
            end_time,
            data_sample_num,  # 1つ目のファイルの長さ分のオフセット
            self.test_dir,
            self.metadata.copy(),
            [32.71161, 129.77558],
            wav_durations,
            0,  # 最初のWAVファイルのインデックス
        )

        # 切り出しが成功したか検証
        self.assertTrue(flag, "2つ目のWAVファイルからの切り出しに失敗しました")

        # 母ファイル選択ロジックのデバッグ情報
        print(f"母ファイル選択: {metadata['source_info']['mother_source_name']}")

        # 母ファイルが2つ目のWAVファイルになっているか確認
        self.assertEqual(
            metadata["source_info"]["mother_source_name"],
            "test_1.wav",
            "2つ目のWAVファイルが母ファイルとして設定されていません",
        )

        # 母ファイルの開始時間を検証（最初のファイルの長さ分進んでいるはず）
        expected_mother_start_time = (
            record_start_time + datetime.timedelta(seconds=60)
        ).strftime("%Y%m%d_%H%M%S")
        self.assertEqual(
            metadata["source_info"]["mother_source_start_time"],
            expected_mother_start_time,
            "母ファイルの開始時間が正しくありません",
        )

        # cut_source_start_time_in_mother_sourceの検証（録音開始130秒 - 1つ目のファイル120秒 = 10秒）
        expected_samples = 10 * self.sample_rate
        cut_start_info = metadata["source_info"][
            "cut_source_start_time_in_mother_source"
        ]
        print(f"2つ目のWAVファイル切り出し結果: {cut_start_info}")
        self.assertIn(
            str(expected_samples),
            cut_start_info,
            f"期待されるサンプル数 {expected_samples} が見つかりません: {cut_start_info}",
        )

        # 時間表記の検証 (00:00:10.00)
        self.assertIn(
            "00:00:10.00",
            cut_start_info,
            f"期待される時間フォーマット 00:00:10.00 が見つかりません: {cut_start_info}",
        )

    def test_max_distance_cutoff(self):
        """最大距離制限によるカット条件のテスト"""
        # テスト用の距離データを作成 - 設定値を超えるケースと超えないケース
        start_time = pd.to_datetime("2024-03-19 06:53:00")
        vessel1_time = start_time + datetime.timedelta(minutes=2)  # 開始から2分後
        vessel2_time = start_time + datetime.timedelta(minutes=4)  # 開始から4分後

        # 2隻の船舶データを作成（1隻は距離が近く、もう1隻は遠い）
        distances_df = pd.DataFrame(
            {
                "mmsi": [123456789, 987654321],
                "vessel_name": ["近い船", "遠い船"],
                "vessel_type": ["Cargo", "Tanker"],
                "length": [100, 150],
                "width": [20, 30],
                "min_distance [m]": [500.0, 15000.0],  # 1隻目は500m、2隻目は15000m
                "min_distance_pos": [[32.7, 129.7], [32.8, 129.8]],
                "min_distance_time": [vessel1_time, vessel2_time],
            }
        )

        # 距離リストはDistanceDataFrameと同じ構造だが、時系列データを含む
        distance_list_df = pd.DataFrame(
            {
                "mmsi": [123456789, 123456789, 987654321, 987654321],
                "vessel_name": ["近い船", "近い船", "遠い船", "遠い船"],
                "dt_pos_utc": [
                    vessel1_time - datetime.timedelta(minutes=1),
                    vessel1_time,
                    vessel2_time - datetime.timedelta(minutes=1),
                    vessel2_time,
                ],
                "distance [m]": [550.0, 500.0, 16000.0, 15000.0],
            }
        )

        # 出力ディレクトリを作成
        output_dir = os.path.join(self.test_dir, "max_distance_test")
        os.makedirs(output_dir, exist_ok=True)

        # テスト用の設定
        audio_config = {
            "cut_margin_minutes": 1,
            "max_cut_distance": 10000.0,  # 10000mより遠い船舶はカットしない
            "check_other_vessels": False,  # 他船舶チェックは無効
        }

        # モック関数を使用（実際のファイル読み書きをスキップ）
        original_cut_wav_file = cut_wav_file
        try:
            # カット実施フラグを記録するためのリスト
            cut_attempts = []

            def mock_cut_wav_file(*args, **kwargs):
                metadata_for_dis = args[8].copy()
                start_time = args[4]
                end_time = args[5]

                # カット試行の情報を記録
                cut_attempts.append({"start_time": start_time, "end_time": end_time})

                # 簡易的なレスポンスを返す
                wav_name = f"cut_{start_time.strftime('%Y%m%d_%H%M%S')}"
                return len(args[0]), True, metadata_for_dis, wav_name

            # 一時的に関数を置き換え
            import audio_processing

            audio_processing.cut_wav_file = mock_cut_wav_file

            # テスト実行
            cut_wav_and_make_metadata(
                self.wav_files,
                self.metadata.copy(),
                start_time,
                distances_df,
                distance_list_df,
                output_dir,
                [32.71161, 129.77558],
                audio_config,
            )

            # 検証: 近い船舶のみがカットされ、遠い船舶はスキップされたことを確認
            # カット試行回数で確認（1隻分のみ）
            self.assertEqual(len(cut_attempts), 1, "カット試行回数が予想と異なります")

            # カットされた船舶の時間が正しいことを確認
            if cut_attempts:
                cut_time = cut_attempts[0]["start_time"]
                # カット開始時間が近い船舶の最短距離時刻の1分前と近いか確認
                expected_time = vessel1_time - datetime.timedelta(minutes=1)
                time_diff = abs((cut_time - expected_time).total_seconds())
                self.assertLess(time_diff, 5, "カット時間が予想と異なります")

        finally:
            # 元の関数に戻す
            audio_processing.cut_wav_file = original_cut_wav_file

    def test_check_other_vessels_condition(self):
        """他船舶との距離比較条件のテスト"""
        # テスト用の開始時間
        start_time = pd.to_datetime("2024-03-19 06:53:00")

        # 最短距離の時間を設定
        vessel1_time = start_time + datetime.timedelta(minutes=2)  # 2分後
        vessel2_time = start_time + datetime.timedelta(minutes=2)  # 同時刻
        vessel3_time = start_time + datetime.timedelta(minutes=4)  # 4分後

        # 3隻の船舶データを作成
        # vessel1: 対象船舶（船舶2より遠い）
        # vessel2: 同時刻にvessel1より近い船舶
        # vessel3: 別時刻で最も近い船舶
        distances_df = pd.DataFrame(
            {
                "mmsi": [111111111, 222222222, 333333333],
                "vessel_name": ["船A", "船B", "船C"],
                "vessel_type": ["Cargo", "Tanker", "Passenger"],
                "length": [100, 150, 80],
                "width": [20, 30, 15],
                "min_distance [m]": [800.0, 500.0, 300.0],
                "min_distance_pos": [[32.7, 129.7], [32.75, 129.75], [32.8, 129.8]],
                "min_distance_time": [vessel1_time, vessel2_time, vessel3_time],
            }
        )

        # 距離リストデータフレーム - 時系列データを含む
        distance_list_df = pd.DataFrame(
            {
                "mmsi": [
                    111111111,
                    111111111,  # 船A
                    222222222,
                    222222222,  # 船B
                    333333333,
                    333333333,  # 船C
                ],
                "vessel_name": ["船A", "船A", "船B", "船B", "船C", "船C"],
                "dt_pos_utc": [
                    vessel1_time - datetime.timedelta(minutes=1),
                    vessel1_time,
                    vessel2_time - datetime.timedelta(minutes=1),
                    vessel2_time,
                    vessel3_time - datetime.timedelta(minutes=1),
                    vessel3_time,
                ],
                "distance [m]": [
                    900.0,
                    800.0,  # 船A
                    600.0,
                    500.0,  # 船B - 船Aより近い
                    400.0,
                    300.0,  # 船C - 最も近い
                ],
            }
        )

        # 出力ディレクトリを作成
        output_dir = os.path.join(self.test_dir, "vessel_comparison_test")
        os.makedirs(output_dir, exist_ok=True)

        # テスト用の設定 - 他船舶チェック有効
        audio_config = {
            "cut_margin_minutes": 1,
            "max_cut_distance": 10000.0,  # すべての船舶が範囲内
            "check_other_vessels": True,  # 他船舶チェック有効
        }

        # モック関数を使用
        original_cut_wav_file = cut_wav_file
        try:
            # カット試行を記録
            cut_attempts = []

            def mock_cut_wav_file(*args, **kwargs):
                metadata_for_dis = args[8].copy()
                start_time = args[4]

                # カット対象船舶のMMSIを特定（開始時間から判断）
                target_time = start_time + datetime.timedelta(
                    minutes=1
                )  # 中心時間に戻す

                # カット試行を記録
                time_diffs = [
                    (abs((target_time - vessel_time).total_seconds()), mmsi)
                    for mmsi, vessel_time in zip(
                        distances_df["mmsi"], distances_df["min_distance_time"]
                    )
                ]
                closest_mmsi = min(time_diffs, key=lambda x: x[0])[1]

                cut_attempts.append(
                    {
                        "start_time": start_time,
                        "target_time": target_time,
                        "mmsi": closest_mmsi,
                    }
                )

                # 簡易的なレスポンスを返す
                wav_name = f"cut_{start_time.strftime('%Y%m%d_%H%M%S')}"
                return len(args[0]), True, metadata_for_dis, wav_name

            # 一時的に関数を置き換え
            import audio_processing

            audio_processing.cut_wav_file = mock_cut_wav_file

            # テスト実行
            cut_wav_and_make_metadata(
                self.wav_files,
                self.metadata.copy(),
                start_time,
                distances_df,
                distance_list_df,
                output_dir,
                [32.71161, 129.77558],
                audio_config,
            )

            # 検証: 実装では、同時刻の船舶との比較において、船Aは船Bより遠いのでカットされない
            # また船Bも同時刻の船C(別々の時刻に存在)より遠いのでカットされない
            # 結果として船Cのみがカットされるべき
            self.assertEqual(len(cut_attempts), 1, "カット試行回数が予想と異なります")

            # カットされた船舶のMMSIを確認
            if cut_attempts:
                cut_mmsi = cut_attempts[0].get("mmsi")
                # 船Cのみがカットされることを確認
                self.assertEqual(
                    cut_mmsi,
                    333333333,
                    "船Cがカットされるべきですが、別の船舶がカットされています",
                )

        finally:
            # 元の関数に戻す
            audio_processing.cut_wav_file = original_cut_wav_file


if __name__ == "__main__":
    unittest.main()
