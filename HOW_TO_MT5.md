# MT5 EAファイル配置・MetaEditorコンパイル手順

## 目的

GitHubから取得したEAコード（`.mq5` / `.mqh`）を、Windows PC側のMT5に配置し、MetaEditorでコンパイルして、MT5で使用できる状態にする。

---

## 前提

この手順は、以下の流れのうち、

```text
1. GitHub DesktopでPull
2. srcの .mq5 / .mqh をコピー
3. MT5の MQL5/Experts に貼り付け
4. MetaEditorで貼り付け後の .mq5 を開く
5. 保存
6. コンパイル
7. MT5でテスト
```

のうち、主に以下を対象とする。

```text
3. MT5の MQL5/Experts に貼り付け
4. MetaEditorで貼り付け後の .mq5 を開く
5. 保存
6. コンパイル
```

---

# 3. MT5の `MQL5/Experts` に貼り付ける手順

## 3-1. MT5を起動する

Windows PCで、実際にEAを動かしたいMT5を起動する。

例：

```text
OANDA MT5
```

複数のMT5をインストールしている場合、必ず**EAを動かしたいMT5**を開く。

---

## 3-2. MT5のデータフォルダを開く

MT5上部メニューから以下を選択する。

```text
ファイル
↓
データフォルダを開く
```

Windowsのエクスプローラーで、MT5専用のデータフォルダが開く。

---

## 3-3. `MQL5/Experts` フォルダを開く

開いたデータフォルダ内で、以下の順にフォルダを開く。

```text
MQL5
↓
Experts
```

最終的に、以下の場所に入る。

```text
...\MQL5\Experts
```

---

## 3-4. GitHub側のEAファイルをコピーする

GitHub DesktopでPullしたローカルリポジトリ内から、対象ファイルをコピーする。

例：

```text
C:\Users\ユーザー名\Documents\GitHub\ea-project\src\EA_13Logic_Integrated.mq5
```

コピーする主なファイル：

```text
EA_13Logic_Integrated.mq5
```

`.mqh` ファイルがある場合は、それも必要に応じてコピーする。

---

## 3-5. `MQL5/Experts` に貼り付ける

コピーした `.mq5` ファイルを、先ほど開いた以下のフォルダへ貼り付ける。

```text
...\MQL5\Experts
```

例：

```text
...\MQL5\Experts\EA_13Logic_Integrated.mq5
```

---

## `.mqh` ファイルがある場合

### シンプル構成の場合

`.mq5` と `.mqh` を同じ `Experts` フォルダに置く。

```text
MQL5/Experts/EA_13Logic_Integrated.mq5
MQL5/Experts/EA_Common.mqh
```

### Includeフォルダを使う構成の場合

`.mqh` を `Include` フォルダに置く。

```text
MQL5/Include/EA_Common.mqh
```

ただし、最初は管理を簡単にするため、できれば **`.mq5` 1ファイル完結** のEAにしておくと安全。

---

# 4. MetaEditorで貼り付け後の `.mq5` を開く手順

## 方法A：MT5からMetaEditorを開く

MT5を開いた状態で、上部メニューから以下を選択する。

```text
ツール
↓
MetaQuotes Language Editor
```

または、キーボードで以下を押す。

```text
F4
```

MetaEditorが開く。

---

## 4-1. MetaEditor左側のナビゲータを確認する

MetaEditor左側に、ナビゲータが表示される。

その中から以下を探す。

```text
Experts
```

---

## 4-2. 貼り付けた `.mq5` を開く

`Experts` の中から、先ほど `MQL5/Experts` に貼り付けたEAファイルを探す。

例：

```text
EA_13Logic_Integrated.mq5
```

対象ファイルをダブルクリックして開く。

---

## 方法B：エクスプローラーから直接開く

`MQL5/Experts` に貼り付けた `.mq5` を右クリックして、以下を選択する。

```text
プログラムから開く
↓
MetaEditor
```

ただし、慣れるまでは **方法A** の方が安全。

理由は、MT5から開くことで、正しいデータフォルダ内のファイルを開いていることを確認しやすいため。

---

# 開いた後の流れ

## 5. 保存する

MetaEditorで `.mq5` を開いたら、まず保存する。

```text
Ctrl + S
```

または、上部メニューから保存する。

```text
ファイル
↓
保存
```

---

## 6. コンパイルする

保存後、MetaEditorでコンパイルする。

方法は以下のどちらか。

```text
コンパイルボタンをクリック
```

または、

```text
F7
```

---

## 6-1. コンパイル結果を確認する

MetaEditor下部のメッセージ欄を確認する。

エラーがない場合、コンパイル成功。

成功すると、同じ `Experts` フォルダ内に `.ex5` ファイルが生成される。

例：

```text
MQL5/Experts/EA_13Logic_Integrated.mq5
MQL5/Experts/EA_13Logic_Integrated.ex5
```

この `.ex5` が、MT5で実際に動作するEAファイル。

---

# 7. MT5側でEAを確認する

MT5に戻り、左側のナビゲータを確認する。

```text
ナビゲータ
↓
エキスパートアドバイザ
```

この中に、コンパイルしたEA名が表示されていればOK。

例：

```text
EA_13Logic_Integrated
```

---

## EAが表示されない場合

ナビゲータ上で右クリックし、以下を選択する。

```text
更新
```

それでも表示されない場合は、以下を確認する。

```text
・.mq5 を MQL5/Experts に貼り付けているか
・MetaEditorでコンパイル成功しているか
・.ex5 が生成されているか
・別のMT5のデータフォルダに貼り付けていないか
```

---

# 注意点

## 複数MT5を使っている場合

OANDA MT5、FXCM MT5など、複数のMT5を入れている場合、それぞれデータフォルダが別になる。

必ず、EAを動かしたいMT5から以下を実行する。

```text
ファイル
↓
データフォルダを開く
```

そのMT5の `MQL5/Experts` に貼り付ける。

---

## GitHubフォルダとMT5フォルダは分ける

GitHub Desktopでcloneしたフォルダを、そのままMT5の `MQL5/Experts` にしない方が安全。

おすすめ構成：

```text
GitHub側：
C:\Users\ユーザー名\Documents\GitHub\ea-project\src

MT5側：
...\MQL5\Experts
```

GitHub側は正本・保管用。  
MT5側はコンパイル・実行用。

---

## MetaEditorで修正した場合の注意

MetaEditorで `MQL5/Experts` 内の `.mq5` を直接修正した場合、その修正はGitHub側には自動反映されない。

そのため、MetaEditorで修正した場合は、必ずGitHub側のファイルにも反映する。

放置すると、以下のようなズレが起きる。

```text
MT5側には修正版がある
GitHub側には古い版しかない
```

基本運用としては、以下がおすすめ。

```text
Mac / ChatGPT側でコード作成・修正
↓
GitHubへ保存
↓
WindowsでPull
↓
MQL5/Expertsへコピー
↓
MetaEditorでは原則、保存・コンパイル・確認のみ
```

---

# 全体手順まとめ

```text
MT5を起動
↓
ファイル
↓
データフォルダを開く
↓
MQL5
↓
Experts
↓
GitHubからコピーした .mq5 を貼り付け
↓
MT5でF4
↓
MetaEditorを開く
↓
左側ナビゲータのExpertsから .mq5 を開く
↓
Ctrl + Sで保存
↓
F7でコンパイル
↓
エラーがないか確認
↓
MT5に戻る
↓
ナビゲータのエキスパートアドバイザを更新
↓
EAが表示されればOK
```
