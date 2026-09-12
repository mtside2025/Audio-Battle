# Audio-Battle

Phase 1〜3（キーボード入力・効果音再生・左右ステレオ音）を実装した、PC向けプロトタイプです。

## ファイル構成

- `/home/runner/work/Audio-Battle/Audio-Battle/audio_battle.py`
  - ゲーム本体（Pygameループ、キー入力、SE再生、左右ステレオ再生）
- `/home/runner/work/Audio-Battle/Audio-Battle/audio_core.py`
  - ステレオ定位の計算ロジック
- `/home/runner/work/Audio-Battle/Audio-Battle/tests/test_audio_core.py`
  - 定位計算の最小ユニットテスト
- `/home/runner/work/Audio-Battle/Audio-Battle/requirements.txt`
  - 実行依存

## 起動方法

1. Python 3.10+ を用意
2. 依存をインストール

```bash
cd /home/runner/work/Audio-Battle/Audio-Battle
python -m pip install -r requirements.txt
```

3. 起動

```bash
python /home/runner/work/Audio-Battle/Audio-Battle/audio_battle.py
```

## 操作

- `Enter`: ゲーム開始アナウンス
- `← / →`: 敵方向のステレオ音（左/右）
- `A / D`: 左/右回避SE
- `J`: 攻撃SE
- `H`: 操作説明の読み上げ
- `Esc` or `Q`: 終了

> 重要情報（方向・操作結果）は音で把握できるようにしてあり、画面は補助表示です。
