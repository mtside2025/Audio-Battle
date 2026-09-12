# Audio-Battle

Phase 1〜6（キーボード入力・左右ステレオ音・敵攻撃・回避/防御・HP）を実装した、PC向けプロトタイプです。

## ファイル構成

- `audio_battle.py`
  - ゲーム本体（Pygameループ、キー入力、戦闘状態、HP、SE再生、左右ステレオ再生）
- `audio_core.py`
  - ステレオ定位の計算ロジック
- `tests/test_audio_core.py`
  - 定位計算の最小ユニットテスト
- `requirements.txt`
  - 実行依存

## 起動方法

1. Python 3.9+ を用意
2. 依存をインストール

```bash
cd Audio-Battle
python -m pip install -r requirements.txt
```

3. 起動

```bash
python audio_battle.py
```

## 操作

- `Enter`: ゲーム開始 / 再スタート
- `← / →`: 敵方向のステレオ音（Phase 1〜3互換）
- `A / D`: 左 / 右攻撃を回避
- `Space`: 防御
- `J / K`: 通常攻撃 / 強攻撃
- `H`: 現在のHPと状態を読み上げ・表示
- `Esc` or `Q`: 終了

> 敵は自動的に左右いずれかから予告音を鳴らして攻撃します。重要情報（方向・攻撃タイミング・操作結果・HP）は音で把握できるようにしてあり、画面は補助表示です。
> pyttsx3 が利用できない環境では、読み上げの代替として通知音で重要イベントを案内します。
> 外部音声ファイルは不要です。音声デバイスが利用できる環境で起動してください。
