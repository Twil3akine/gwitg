<p align="center">
  <img src="./assets/gwitg_logo.png" alt="gwitg logo" width="420">
</p>

<p align="center">
  <strong>Delegate independent work to subagents without turning the parent agent into a progress monitor.</strong>
</p>

<p align="center">
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://github.com/Twil3akine/gwitg/releases"><img src="https://img.shields.io/github/v/release/Twil3akine/gwitg" alt="GitHub release"></a>
</p>

<p align="center">
  <a href="./README.en.md">English</a> | <strong>日本語</strong>
</p>

# gwitg

`gwitg`は、**OpenAI Codex向け**に、独立した作業をサブエージェントへ委任し、必要に応じて並列実行するためのAgent Skillです。

中心となる考え方は、**作業を任せた後に親エージェントが進捗監視を続けないこと**です。親エージェントは結果を待つ間、別の独立した作業を進めます。

```text
parent agent
├─ investigate-api
├─ tests
└─ review

        ↓ completed results

parent integrates and validates
```

状態確認そのものは禁止しませんが、短い間隔でのポーリングや途中ログを使った進捗監視は行いません。詳しい運用ルールは[SKILL.md](SKILL.md)に定義しています。

## 対応環境

現在の`gwitg`は**OpenAI Codex向け**です。`/subagent`、worker model、reasoning effortなど、Codexのsubagent機構と操作を前提にしています。

Claude Code、Cursor、Copilotなどでの動作は現時点では対応・検証していないため、汎用的なcross-agent skillとしては扱いません。

## Quick Start

### ユーザー単位で使う

```sh
git clone https://github.com/Twil3akine/gwitg ~/.codex/skills/gwitg
```

### 特定のリポジトリだけで使う

対象リポジトリで実行します。

```sh
mkdir -p .codex/skills
git clone https://github.com/Twil3akine/gwitg .codex/skills/gwitg
```

Codexへ明示的に指定する場合は、次のように依頼します。

```text
gwitgを使ってこの作業を進めて
```

スキルの自動選択に任せることもできます。

## どう動くか

親エージェントは、頻繁な同期が不要で、目的と完了条件を明確にできる作業をサブエージェントへ委任します。

典型的には次のような作業が対象です。

- repository investigation
- bug investigation
- well-defined implementation
- test writing
- independent code review
- documentation investigation
- codebase search
- self-contained experiments
- validation against explicit acceptance criteria

独立した作業が複数あれば、依存関係が許す範囲で並列に実行します。

作業で使うworker profileをユーザーが明示した場合は、その指定を優先します。明示がなく、委任判断またはprofile選択が曖昧な場合は、有効な共通形式による判断役の推薦profileを使います。それ以外で親が委任を決めたときは既定の`standard`を使います。profile名と解決したモデル・推理レベルを一緒に保持し、再帰委任する子にも渡します。子は同じprofileと解決値を使い、設定を読み直しません。組み込みの`standard`は`6-luna`・`high`です。実行環境で使えない設定を別の値へ黙って置き換えません。 `/fast`は環境の既定値を使います。

### 実行中のルール

作業を任せた後も、必要であれば`running`、`completed`、`failed`などの状態を確認できます。

ただし、次のような監視は行いません。

- 短い間隔で状態確認を繰り返す
- sleepとstatus確認を交互に行う
- 途中ログやpartial outputを確認する
- 遅いという理由だけで再起動・差し替え・モデル変更を行う

完了通知を待つ操作は許可されます。

### 実行中に伝えられること

親エージェントから実行中のsubagentへ追加で伝えられるのは、次の3種類です。

- 誤った前提の訂正
- 新たに判明した制約
- 作業の中止

目的・成果物・作業方針を変える通常の追加指示には使いません。

訂正や制約により元の依頼を続けられなくなった場合、subagentは理由を報告して停止します。

## Delegation Judge

委任するか、使うprofileを決めにくい場合に限り、外部のdecision modelを判断役として利用できます。委任とprofileの両方が明らかな作業では外部モデルを呼びません。

利用できる値は次の3つです。

| 値 | 判断役 |
| --- | --- |
| `clef` | 利用環境のClef判断ツール |
| `jev` | 利用環境のJev判断ツール |
| `none` | 親エージェント自身 |

判断役の優先順位は次のとおりです。

```text
1. ユーザーがその作業で明示した指定
2. <project-root>/.gwitg/decision-model
3. ~/.config/gwitg/decision-model
4. none
```

プロジェクト設定が存在する場合は、ユーザー共通設定より優先されます。

### 共通設定

例えば、通常はClefを使う場合は次のように設定します。

```sh
mkdir -p "$HOME/.config/gwitg"
printf '%s\n' clef > "$HOME/.config/gwitg/decision-model"
```

### プロジェクトごとの上書き

特定のリポジトリだけ別の判断役を使う場合は、プロジェクトルートに設定します。

```sh
mkdir -p .gwitg
printf '%s\n' jev > .gwitg/decision-model
```

外部の判断役を使わない場合は`none`を指定します。

```sh
printf '%s\n' none > .gwitg/decision-model
```

設定ファイルは作業開始時に一度だけ読み、その作業中は同じ判断役を利用します。子エージェントにも選択結果を渡すため、同じ作業の中で設定ファイルを繰り返し読みません。

設定値が不正、読み取り不能、または選択した外部判断ツールを利用できない場合は、その事実を伝えて親エージェントが判断します。ClefからJev、JevからClefへ無断で切り替えることはありません。

この設定は外部モデルへの接続自体を用意するものではありません。ClefやJevを実際に呼び出せるツールや接続は、利用環境側に必要です。

設定解決には次のスクリプトを使います。

```sh
python3 /path/to/gwitg/scripts/decision_model.py
```

スキルのディレクトリへ移動せず、作業対象のディレクトリから絶対パスで実行します。

### 判断役の共通出力

判断役の結果は、次の3項目を持つ共通形式に読み替えます。

```yaml
delegate: true
profile: light
reason: Independent repository search with bounded scope
```

`delegate`は必須の真偽値です。委任する場合の`profile`は設定済みworker profile名、委任しない場合は`null`です。`reason`には空でない短い説明を入れます。項目の欠落、型違い、空の理由、委任とprofileの矛盾、未定義の項目があれば結果全体を無効とし、親エージェントが判断します。無効な結果から一部の値だけを採用しません。

判断役は具体的なモデル名、推理レベル、`/fast`の状態を指定しません。親エージェントが最終的な委任を決め、profileの解決とworker設定は別に行います。ClefやJevの呼び出し方は各環境に委ねます。

## Worker Profiles

worker profileは、workerのモデルと推理レベルをまとめた名前です。組み込みprofileは`light`、`standard`、`strong`です。既定値は`standard`で、従来の`6-luna`・`high`を保ちます。判断役は具体的な設定ではなくprofile名だけを推薦します。`/fast`はprofileとは別の設定です。

profile設定はプロジェクトルートの`.gwitg/worker-profiles.json`を先に読み、存在しない場合のみ共通設定`~/.config/gwitg/worker-profiles.json`を読みます。どちらもなければ組み込み設定を使います。採用した設定ファイルの一覧全体を使い、複数設定を合成しません。プロジェクトファイルが不正・読み取り不能な場合はエラーとし、共通設定へ切り替えません。

```json
{
  "profiles": {
    "light": {"model": "6-luna", "reasoning_effort": "low"},
    "standard": {"model": "6-luna", "reasoning_effort": "high"},
    "strong": {"model": "6-astra", "reasoning_effort": "high"}
  }
}
```

選んだprofileの設定は、作業対象ディレクトリから次のように解決できます。引数を省略すると`standard`を使います。

```sh
python3 /path/to/gwitg/scripts/worker_profiles.py light
```

resolverは設定値をそのまま返し、実行環境で利用できるかは確認しません。明示profileや有効な推薦profileが存在しない場合、または設定が不正な場合はエラーとして扱い、別profileへ黙って切り替えません。プログラムから共通形式を渡す方法など、詳細は[SKILL.md](SKILL.md)を参照してください。

### Workerの起動

起動前に、利用中のspawnツールが受け付けるモデルID、推理レベル、会話履歴の引き継ぎ方を確認します。例えばツールが`gpt-6-luna`と`gpt-6-astra`を対応IDとして示す環境では、組み込みの`light`と`standard`は`gpt-6-luna`、`strong`は`gpt-6-astra`で起動します。この対応は実行環境に依存します。IDに接頭辞を機械的に足したり、別の値へ置き換えたりしません。選択したprofile名、resolverの値、起動IDを子にも引き継ぎます。

モデルや推理レベルを指定するために`fork_turns="none"`が必要なツールでは、その値と両方の設定を明示します。会話履歴を渡さない場合、作業指示には目的と完了条件、作業ディレクトリ、関連ファイル、現状と制約、変更可能な範囲、検証方法、報告内容を含めます。さらに選択済みの判断役とprofile、解決値、起動ID、適用するgwitgルールを渡し、子が過去の会話を読めることを前提にしません。選んだ設定で起動できない場合は、親が作業します。

## Recursive Delegation

subagentも、割り当てられた作業の中に独立したsubtaskがある場合は、さらにsubagentへ委任できます。

```text
parent
├─ investigate-api
│  ├─ inspect-cache
│  └─ inspect-tests
└─ implementation
```

再帰的に委任する場合も、選択済みのprofile名と解決した設定を引き継ぎ、同じno-pollingルールと介入制限を適用します。

子を持つsubagentは、子の完了結果を統合してから親へ完了報告します。

## `/subagent`によるユーザー操作

ユーザーは`/subagent`から実行中のsubagentを直接確認・操作できます。

gwitgで許可する操作は次の4種類です。

1. 現在の状態を確認する
2. スレッドを開く
3. `/fast`を有効・無効にする
4. モデルまたは推理レベルを変更する

親エージェントは、スレッドを開く操作や`/fast`・model・reasoning effortの変更を代理しません。

実行中workerの差し替え、目的変更、作業方針変更はこれらの例外に含まれません。

## Investigation Reports

時系列や情報の鮮度が重要な調査では、必要に応じて次を区別して報告します。

- 何を確認したか
- いつ確認したか
- 証拠がどの時点の情報を示しているか
- 現在状態を直接確認した事実か、過去の文書・ログか
- 未確認事項と制約

今日読んだ文書でも、その内容が今日の状態を示しているとは限りません。情報の時点が分からない場合は推測せず、不明とします。

単純なコード調査では、必要な項目だけを報告し、長い固定テンプレートは要求しません。

## Repository Layout

```text
gwitg/
├── assets/
│   └── gwitg_logo.png
├── LICENSE
├── README.md
├── README.en.md
├── SKILL.md
├── scripts/
│   ├── decision_model.py
│   └── worker_profiles.py
└── tests/
    ├── test_decision_model.py
    └── test_worker_profiles.py
```

- [LICENSE](LICENSE): MIT License
- [SKILL.md](SKILL.md): エージェントが従う運用ルール
- [scripts/decision_model.py](scripts/decision_model.py): decision model設定の解決
- [tests/test_decision_model.py](tests/test_decision_model.py): 設定解決のテスト

## Test

```sh
python3 -m unittest discover -s tests -v
```

## Links

- [Releases](https://github.com/Twil3akine/gwitg/releases)
- [Issues](https://github.com/Twil3akine/gwitg/issues)
- [OpenAI: Skills](https://developers.openai.com/api/docs/guides/tools-skills)
- [OpenAI: Build skills](https://developers.openai.com/plugins/build/skills)
- [OpenAI: Multi-agent](https://developers.openai.com/api/docs/guides/responses-multi-agent)
- [Agent Skills specification](https://agentskills.io/)
