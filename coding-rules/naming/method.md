# ネーミング規約：メソッド

- 分類: ネーミング規約 / メソッド
- タグ: #コーディング規約 #Java #命名規約
- 取込元: コーディング規約.xlsx / Sheet3

## 規約

- コンストラクタと同じ名前のメソッドはつくらない。
- メソッド名は区切りのみ大文字にする。
- 変換メソッド名は「to + オブジェクト名」にする。
- ゲッターメソッド名は「get + 属性名」にする。
- 型が boolean の場合は「is + 属性名」にする。
- セッターメソッド名は「set + 属性名」にする。
- boolean 変数を返すメソッド名は true / false の状態がわかるようにする。

## 良い例

```java
public String getName() {
    //・・・
}

public String toString() {

public boolean isAsleep() {
}
public boolean exists() {
}
public boolean hasExpired() {
}
```

## 悪い例

```java
public String getname() {
    //・・・
}
public String GETNAME() {
    //・・・
}

public String string() {
```
