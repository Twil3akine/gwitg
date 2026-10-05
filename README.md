# gwitg

`gwitg`は、Codexが独立した作業をサブエージェントに並列で任せるためのAgent Skillです。サブエージェントは、親エージェントから作業を任されて動く別のエージェントです。

基本方針は、**作業を任せたら、完了または明示的な失敗通知が届くまで監視しない**ことです。親エージェントは、その間に独立した別の作業を進められます。詳しいルールは[SKILL.md](SKILL.md)に記載しています。

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

サブエージェントの既定設定は、モデルが`6-luna`、推理レベルが`high`です。この設定を選べない環境では、別の設定へ黙って変更せず、ユーザーの明示的な指示に従うか、現在のエージェントが作業を続けます。

作業を任せた後、親エージェントは途中の状態や出力を確認しません。完了または明示的な失敗通知を待ち、完了した結果を確認して統合します。応答がないことや時間がかかっていることだけでは、失敗と判断しません。

サブエージェントも、必要に応じて別のサブエージェントに作業を任せられます。その場合も、同じ設定と監視しないルールを適用します。

作業を任せてよいか判断が難しい場合は、利用可能であれば`Jev`または`Clef-flah-q4`に判断を補助してもらえます。

### 実行中のサブエージェントを操作する

ユーザーが実行中のサブエージェントを確認・操作する場合は、`/subagent`を直接使ってください。`gwitg`のルールで認める操作は、次の4種類です。

1. 現在の状態を確認する
2. スレッドを開く
3. `/fast`を有効・無効にする
4. モデルまたは推理レベルを変更する

親エージェントに状態確認や設定変更を代行させることは禁止しています。エージェントの差し替え、停止・再開、追加指示は、認める操作に含めません。

## ファイル構成

```text
gwitg/
├── README.md
└── SKILL.md
```

[SKILL.md](SKILL.md)に、エージェントが従う運用ルールを定義しています。

## 参考資料

- [OpenAI: Skills](https://developers.openai.com/api/docs/guides/tools-skills)
- [OpenAI: Build skills](https://developers.openai.com/plugins/build/skills)
- [OpenAI: Multi-agent](https://developers.openai.com/api/docs/guides/responses-multi-agent)
- [Agent Skills specification](https://agentskills.io/)
