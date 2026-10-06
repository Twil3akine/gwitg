# gwitg

`gwitg`は、Codexが独立した作業をサブエージェントに並列で任せるためのAgent Skillです。サブエージェントは、親エージェントから作業を任されて動く別のエージェントです。

基本方針は、**作業を任せたら進捗を監視せず、状態確認のポーリングをしない**ことです。親エージェントは、その間に独立した別の作業を進められます。詳しいルールは[SKILL.md](SKILL.md)に記載しています。

## インストール

利用範囲に合わせて、次のどちらかを選んでください。

### ユーザー単位で使う

```sh
git clone https://github.com/Twil3akine/gwitg ~/.codex/skills/gwitg
```

Codexがユーザー単位で利用するスキルの配置先は、`~/.codex/skills/<skill-name>/SKILL.md`です。

### 特定のリポジトリだけで使う

対象のリポジトリ内で実行してください。

```sh
mkdir -p .codex/skills
git clone https://github.com/Twil3akine/gwitg .codex/skills/gwitg
```

## 使い方

Codexに、`gwitg`の使用を明示的に指示します。

```text
gwitgを使ってこの作業を進めて
```

明示的に指示せず、Codexによるスキルの自動選択に任せることもできます。

### 作業の進め方

親エージェントは、頻繁なやり取りが不要な独立した作業をサブエージェントに任せます。独立した作業が複数あれば、可能な限り並列で進めます。

作業で使うprofileをユーザーが明示した場合は、その指定を既定の`standard`より優先します。指定がなければ`standard`を使います。profile名と解決したモデル・推理レベルを一緒に保持し、再帰委任する子にも渡します。子は同じprofileと解決値を使い、設定を読み直しません。組み込みの`standard`は`6-luna`・`high`です。実行環境で使えない設定を別の値へ黙って置き換えません。

作業を任せた後も、必要に応じて実行中・完了・失敗などの状態を確認できます。ただし、短い間隔で状態確認を繰り返すポーリングや、途中の出力・ログを使った進捗監視は禁止します。完了通知を待つ操作は許可します。応答がないことや時間がかかっていることだけでは、失敗と判断しません。

実行中に伝えられるのは、誤った前提の訂正、新たに判明した制約、作業の中止に限ります。目的・成果物・作業方針の変更や、通常の追加作業には使いません。訂正や制約により元の依頼を続けられない場合は、サブエージェントが理由を報告して停止します。

調査結果には、必要に応じて確認対象、確認日時と情報が示す時点、直接確認した事実か過去の記録か、未確認事項を含めます。時系列が重要な調査では現在の事実と過去の記録を区別し、情報の時点が不明なら不明と書きます。

サブエージェントも、必要に応じて別のサブエージェントに作業を任せられます。その場合も、同じ設定と監視しないルールを適用します。

委任するか、使うprofileを決めにくい場合は、次の設定で判断役を選べます。委任とprofileの両方が明らかな作業では外部モデルを呼びません。

### 判断役を選ぶ

最初に共通設定の`~/.config/gwitg/decision-model`を読みます。このファイルがない場合だけ、プロジェクトルートの`.gwitg/decision-model`を読みます。どちらもなければ`none`を使います。

プロジェクトルートは、作業開始ディレクトリが属するGitリポジトリのルートです。Git管理外の場合や、Gitを利用できない・ルートを取得できない場合は、作業開始ディレクトリを使います。共通設定が`none`の場合も、プロジェクト設定より優先されます。

ファイルに書く値は、次のいずれか1つです。

| 値 | 委任判断の担当 |
| --- | --- |
| `clef` | 利用環境のClef判断ツール |
| `jev` | 利用環境のJev判断ツール |
| `none` | 親エージェント自身 |

例えば、Clefを使う場合は次を実行します。すでに設定がある場合は、このコマンドで上書きされます。

```sh
gwitg_config_dir="$HOME/.config/gwitg"
mkdir -p "$gwitg_config_dir"
printf '%s\n' clef > "$gwitg_config_dir/decision-model"
```

共通設定を作らずプロジェクトごとに選ぶ場合は、プロジェクトルートの`.gwitg/decision-model`に同じ値を書きます。

Jevを使う場合は`clef`を`jev`に、外部の判断役を使わない場合は`none`に変更します。設定ファイルがない場合の既定値も`none`です。ユーザーがその作業で判断役を明示した場合は、ファイルより明示指定を優先します。

設定ファイルは作業開始時に一度だけ読み、その作業中は同じ判断役を使います。サブエージェントにも選択結果を渡すため、同じ作業で読み取りを繰り返しません。ファイルの変更は、次の別の作業を開始したときに反映されます。作業の続きや状況確認は、新しい作業として扱いません。作業中にユーザーが判断役を明示した場合は、その指定を優先します。

常駐プロセスは不要で、選択結果を別の作業へ持ち越しません。設定ファイルを読む処理は、ユーザーの設定を変更しません。

空ファイル、不正な値、読み取り失敗は作業開始時に知らせ、その作業では`none`として親エージェントが判断します。共通設定の読み取りに失敗しても、プロジェクト設定へ切り替えません。判断のたびに読み取りを再試行しません。選んだ判断ツールが利用できない場合も、その事情を伝えて親エージェントが判断し、別の外部モデルへ無断で切り替えません。

この設定はClefやJevへの接続を用意するものではありません。対応するツールや接続が利用環境に必要です。workerの設定は別途worker profileから解決します。組み込みの`standard`は従来の`6-luna`・`high`を保ち、カスタム設定がある場合はその値を使います。

### 判断役の共通出力

Clef、Jev、または将来の判断役の結果は、共通形式に読み替えて扱います。形式には常に次の3項目を含めます。

```yaml
delegate: true
profile: light
reason: Independent repository search with bounded scope
```

`delegate`は必須の真偽値、`profile`は必須項目、`reason`は必須の短い説明です。`delegate: true`の場合、`profile`にはworker profile名を指定し、`delegate: false`の場合は`null`にします。profile名は設定済みprofileを参照する名前であり、設定にない名前は後続処理で解決できません。

形式の欠落、型違い、空の理由、または委任の有無とprofileの組み合わせが不正な結果は無効として扱います。無効な結果から一部の値だけを採用せず、判断役の結果は利用できないものとして親エージェントが判断します。未定義の項目も受け付けません。

判断役は具体的なモデル名、推理レベル、`/fast`の状態を出力しません。これらはworker profileの設定と実行環境に属します。ClefやJevの接続方法や呼び出し方も共通形式には含めず、各判断役の利用環境に委ねます。親エージェントが最終的な委任を決めます。

設定の読み取りにはPython 3を使います。作業対象のディレクトリから、スキル配置先のスクリプトを絶対パスで指定してください。スキルの配置先に移動すると、その場所を基準にプロジェクトを探してしまいます。

```sh
python3 /path/to/gwitg/scripts/decision_model.py
```

Python 3や読み取りスクリプトを利用できない場合は、その事情を伝えて親エージェントが判断します。

### worker profile

worker profileは、作業者のモデルと推理レベルをまとめた名前です。初期プロファイルは`light`、`standard`、`strong`です。選択の優先順位は、ユーザーが明示したprofile、委任またはprofile選択が曖昧な場合に得た有効な共通形式の推薦profile、既定の`standard`です。組み込みの`standard`は従来の`6-luna`・`high`を保ちます。判断役はprofile名だけを推薦し、具体的な設定はworker profileから解決します。`/fast`はprofileとは別の設定です。

親エージェントは、選んだprofile名とresolverが返すモデル・推理レベルを組にして作業中保持し、子へ渡します。再帰委任でもこの組をそのまま引き継ぎます。明示されたprofileや有効な推薦profileを解決できない場合はエラーとして扱い、別のprofileへ置き換えません。共通形式が無効なら結果全体を利用せず、親エージェントが判断します。`delegate: false`はprofileを解決せず、親エージェントが最終判断します。有効な推薦profileの設定を読み込めても、実行環境がそのモデルや推理レベルを実際に利用できるかはresolverでは保証できません。利用できないと分かった場合は設定を置き換えずに委任を中止するか、親エージェント自身が作業します。

profileは共通設定`~/.config/gwitg/worker-profiles.json`、またはプロジェクト設定`.gwitg/worker-profiles.json`で変更できます。共通設定があればそちらを使い、なければプロジェクト設定を使います。どちらもなければ次の組み込み設定を使います。

```json
{
  "profiles": {
    "light": {"model": "6-luna", "reasoning_effort": "low"},
    "standard": {"model": "6-luna", "reasoning_effort": "high"},
    "strong": {"model": "6-astra", "reasoning_effort": "high"}
  }
}
```

設定ファイルに書いたprofile一覧は組み込み一覧を置き換えます。各profileには`model`と`reasoning_effort`を指定してください。指定された値はそのまま返します。利用できない設定を別のモデルや推理レベルへ置き換えません。JSONや設定項目が不正な場合、または選択したprofileが存在しない場合はエラーになります。

選んだprofileの具体的な設定を確認するには、次のコマンドにprofile名を渡します。たとえば判断役の有効な推薦が`light`で、親エージェントが採用した場合は`light`を指定します。引数を省略すると`standard`を使います。

```sh
python3 /path/to/gwitg/scripts/worker_profiles.py light
```

プログラムから共通形式を扱う場合は、解析済みの辞書を`resolve_worker_profile(judge_result=...)`へ渡せます。ユーザーがprofileを明示したときは、そのprofile引数を優先し、判断役の結果は参照しません。有効な`delegate: false`ならworker設定を解決せず、無効な結果は`InvalidJudgeResult`、有効でも未設定のprofile名は通常のprofile解決エラーになります。どちらも既定profileへ黙って切り替えません。

### 実行中のサブエージェントを操作する

ユーザーが実行中のサブエージェントを確認・操作する場合は、`/subagent`を直接使ってください。`gwitg`のルールで認める操作は、次の4種類です。

1. 現在の状態を確認する
2. スレッドを開く
3. `/fast`を有効・無効にする
4. モデルまたは推理レベルを変更する

親エージェントは、ポーリングにならない状態確認と、上記の訂正・制約追加・中止を伝えられます。スレッド閲覧、`/fast`やモデル・推理レベルの変更は代行しません。実行中のエージェントの差し替えや、中止した作業の再開、目的・作業方針を変える追加指示は、これらの例外に含めません。

## ファイル構成

```text
gwitg/
├── README.md
├── SKILL.md
├── scripts/
│   ├── decision_model.py
│   └── worker_profiles.py
└── tests/
    ├── test_decision_model.py
    └── test_worker_profiles.py
```

[SKILL.md](SKILL.md)に、エージェントが従う運用ルールを定義しています。

## 設定読み取りのテスト

```sh
python3 -m unittest discover -s tests -v
```

## 参考資料

- [OpenAI: Skills](https://developers.openai.com/api/docs/guides/tools-skills)
- [OpenAI: Build skills](https://developers.openai.com/plugins/build/skills)
- [OpenAI: Multi-agent](https://developers.openai.com/api/docs/guides/responses-multi-agent)
- [Agent Skills specification](https://agentskills.io/)
