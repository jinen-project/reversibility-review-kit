# Reversibility Review Kit / 可逆性レビュー・キット

Bounded review specimens for asking whether a proposed change narrows exit, recovery, or future alternatives.

変更案が退出・回復・将来の別解可能性を狭めていないかを読むための、限定的な検査標本です。

## Current release

The original prototype has 109 passing local tests. This repository now contains a clean, standard-library-only export of its review engine and test suite under `examples/review-engine`.

元の試作にはローカルで109件の通過テストがあります。ここには、出所を確認した標準ライブラリのみのエンジンとテスト束を `examples/review-engine` として置いています。

## Run the example / 実行例

```sh
cd examples/review-engine
python3 -m unittest discover -v
```

The code accepts abstract observations and proposed placements, then returns a bounded review packet about closure, reversibility, recovery, and accumulated concentration. The test data is synthetic.

抽象化した観測と変更案から、閉鎖・可逆性・回復・集中の観測パケットを返します。テストデータは合成です。

## Not a claim

It does not predict the future, make adoption decisions, or establish real-world safety.

未来予測、採用判断、現実世界での安全性の証明ではありません。
Bilingual review specimens for examining reversibility and closure risks in change proposals.
