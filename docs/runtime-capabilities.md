# サブエージェントのランタイム情報

この調査は2026-10-07に行いました。対象は、このCodex会話で利用できる `collaboration` ツール、ローカルの `codex` CLI 0.160.0のヘルプ、OpenAI公式ドキュメントです。実行中のサブエージェント一覧はメタデータ確認のため一度だけ取得しました。途中出力やスレッドは開いていません。

## 現在の会話ランタイム

「直接」はツール仕様または一度の直接観測で値を取得できること、「派生」は公開された値から計算できること、「ランタイム依存」は作成時の指定か別のUIに限られること、「不可」は確認した現在のツール面に取得手段がないことを表します。

| 情報 | 判定 | 根拠と限界 |
| --- | --- | --- |
| 親子関係 | 派生 | 一覧の `agent_name` は `/root/issue_5` のような階層付き名前でした。スラッシュ区切りから親を推定できますが、親IDフィールドはありません。 |
| canonical worker name | 直接 | 一覧の `agent_name` に安定した人間可読名が含まれます。末尾の `task_name` は名前から取り出せます。 |
| 独立したalias | 不可 | `agent_name` と別の表示名を取得する欄はありません。 |
| lifecycle | 直接 | `list_agents` はエージェント名と状態を返し、今回の一度の取得では `running` を観測しました。状態の反復取得を前提にしません。 |
| task summary | ランタイム依存 | 起動時には作業指示を渡しますが、一覧には含まれません。現在のツール面に既存workerの指示を読む手段はありません。 |
| thread | ランタイム依存 | `collaboration` ツールにスレッドを開く操作はありません。SKILL.mdに記載した `/subagent` のユーザー操作は、対応するUIから利用します。 |
| model | ランタイム依存 | 起動時に任意の `model` を指定できますが、一覧や照会ツールで現在値を取得できません。 |
| reasoning effort | ランタイム依存 | 起動時に任意の `reasoning_effort` を指定できますが、一覧や照会ツールで現在値を取得できません。 |
| `/fast` | ランタイム依存 | 現在のツール仕様に切替または状態取得の手段はありません。SKILL.mdの `/subagent` 操作は、対応するユーザーUIから利用します。 |
| start time | 不可 | 一覧にも他の現在のツール仕様にも開始時刻はありません。 |
| cancellation | 直接 | `interrupt_agent` があり、呼び出し結果に直前の状態が含まれます。これは中止操作であり、状態確認の代用ではありません。 |

## 将来の読み取り専用TUIが依存できる最小データ

現在の会話ランタイム向けTUIが使える最小データは、一覧から直接得るcanonical worker nameとlifecycle、名前の階層から派生する親子関係です。task summary、thread、model、reasoning effort、`/fast`、start timeなど取得元が確認できない項目は `unknown` と表示します。これらの値の取得元はagent tool内の `list_agents` に限られ、単独CLIから同じランタイムへ接続するbridgeは確認できていません。

ユーザーが明示的に開いたときの単発snapshotを表示できます。自動更新や親エージェントによる定期取得は行わず、TUIの利用を進捗監視のためのポーリングにしません。

## CLIと別ランタイムの公開API

ローカル `codex agents --help` は、同じローカルapp-server daemon上のagent sessionを閲覧するCLIと説明しています。`codex app-server --help` では、app-serverを起動するサブコマンドを確認しました。今回確認できたCLIヘルプには、この会話ランタイムの `collaboration` 一覧を取得する方法や、現在の会話に接続する方法は記載されていません。したがって、これらのCLIから現在の会話のworker情報を取得できるとは確認できませんでした。

OpenAI Agents APIには、Agents APIで作成したセッションのサブエージェントを取得する公開エンドポイントがあります。公式スキーマには `parent_agent_id`、`name`、`status`、`instructions`、`opened_at` があり、入れ子と終了済みworkerも一覧に含まれます。さらに、subagentのitems/turnsエンドポイントも公式APIリファレンスで確認しました。[Subagents API](https://developers.openai.com/api/reference/typescript/resources/beta/subresources/agents/subresources/sessions/subresources/subagents/methods/list)と[Agents API概要](https://developers.openai.com/api/docs/guides/agents-api/overview)に記載されています。このAPIはOpenAI管理のCodex harnessが持つAgents API session用です。同じ公開ページは、アプリがそのセッションを作成し、イベントを受け取る別の管理面として説明しています。現在の会話ランタイムと接続するAPIだとは確認できていません。

## Issue #6への結論

Issue #6の「現在のサブエージェント階層」を対象にする読み取り専用TUIは、現状の公開情報だけでは単独CLIとして実装できると確認できません。現在の会話内で `collaboration` ツールを呼べるホストなら、限定された値を表示する設計は可能です。ローカルCLIやAgents APIからこの会話のworkerを読む接続方法は確認できていないため、現段階でそこを前提にしたTUIは実装できません。

別案として、対象をAgents APIのsessionに限定するTUIは、公開されたsubagents/items/turns APIを使う別製品として実装可能です。ただし、そのデータを現在の会話ランタイムの情報と混同してはいけません。どちらのTUIも、利用可能な取得方法が確認された値だけを表示し、取得できない値は `unknown` とします。
