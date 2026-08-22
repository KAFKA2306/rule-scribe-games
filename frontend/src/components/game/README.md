# Game Components

ゲーム詳細ページの小さな再利用componentだけを置きます。ルールのtruthはcomponent内へ複製せず、GamePageが選択RuleSetのpresentation projectionを受け取って表示します。

- `ConceptGlossary.jsx`: canonical Concept/glossary read
- `RuleAskPanel.jsx`: 選択中presentation projectionだけを使うrule lookup
- `ExternalLinks.jsx`: catalog external links
- `ShareButtons.jsx`: share actions
- `TextToSpeech.jsx`: 現在表示中のテキスト読み上げ
- `AddToListButton.jsx` / `OwnedGameButton.jsx`: user list state
