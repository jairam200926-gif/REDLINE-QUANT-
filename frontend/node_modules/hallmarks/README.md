# Hallmarks

**Spot it before you read it.**

Hallmarks turn long, opaque identifiers — crypto addresses, key fingerprints, commit SHAs, anything you'd otherwise read character by character — into small, distinct visual marks. A glance is enough to tell whether two strings are the same.

Site: **[hallmarks.info](https://hallmarks.info)**

This repository contains:

- [**`SPEC.md`**](SPEC.md) — the Hallmarks v1.0 specification.
- [**`hallmark.ts`**](hallmark.ts) — TypeScript reference implementation. Bundles to a small ES module for the web; also runs in Node.
- [**`Sources/Hallmarks/Hallmark.swift`**](Sources/Hallmarks/Hallmark.swift) — Swift reference implementation (SwiftUI), available as a SwiftPM package via `Package.swift` at the repo root.
- [**`test-vectors.json`**](test-vectors.json) — frozen conformance vectors. An implementation conforms if it reproduces every vector exactly.
- [**`index.html`**](index.html) — the project website (live at [hallmarks.info](https://hallmarks.info)).

## What it produces

For every input string, a Hallmark is a coordinated set of three outputs derived from a single SHA-256 hash:

- A **visual pattern** — a 5×7 left-right-symmetric grid of dots, in one of three styles (standard / high-contrast / monochrome), rendered as SVG. Built for sizes from 22 px to whatever you need.
- A **verbal companion** — three BIP-39 English words (e.g. `violin orbit tangerine`), suitable for screen readers, phone-call verification, or display as a sub-caption.
- A **14×20 pixel-art rendering** — a hard-edged pixel grid for hardware wallets, e-ink, embedded LCDs, and any display where sub-pixel rendering isn't available.

## Quick start

### JavaScript / TypeScript

```bash
npm install hallmarks
```

```ts
import { hallmark, hallmarkWords, hallmarkPixels } from "hallmarks";

const node = hallmark("bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq");
document.querySelector("#avatar").appendChild(node);

hallmarkWords("bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq");
// → ["brush", "swarm", "always"]

hallmarkPixels("bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq");
// → Uint8Array(280) — 14×20 pixel raster
```

### Swift

```swift
// Package.swift
.package(url: "https://github.com/GBKS/hallmarks", from: "1.0.0")
```

```swift
import Hallmarks

Hallmark(input: "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq")
    .frame(width: 64)
```

## Why this exists

Most identicon systems were designed to be avatars — small images that give an account a recognizable face. Hallmarks were designed for a different job: **verifying that two identifiers are the same**.

That distinction changes the design. Hallmarks need to differ dramatically when the input differs by even one character (SHA-256 avalanche). They need to stay distinct at very small sizes (22 px and below). They need a verbal channel so blind users and voice calls can take part in the comparison. They need a pixel-perfect mode for hardware wallets. And they need to look the same on every platform — byte-identical, forever — so a comparison across devices is meaningful.

## Conformance

This repository ships two reference implementations. Both produce byte-identical output for the same input. To verify a third implementation, run it against [`test-vectors.json`](test-vectors.json) — every entry must match exactly.

## License

The Hallmarks v1.0 specification (`SPEC.md`) and the conformance test vectors (`test-vectors.json`) are dedicated to the **public domain under CC0 1.0** — anyone may implement them freely, without attribution. The reference implementations, the website, and the rest of this repository are released under the **MIT License**. See [`LICENSE`](LICENSE) for details.

The dual licensing is intentional: implementers should never feel constrained by the spec itself, and corporate adopters get the familiar MIT terms for the code.

## Status

Hallmarks v1.0 is a draft. The bit-level algorithm is frozen; only the prose may evolve between draft and final. If you build something that depends on Hallmarks, pin to a specific spec version.

## Background

Hallmarks grew out of [Arké](https://arke.cash), an experimental Bitcoin and Ark wallet I've been building, where sending money to long, look-alike addresses needed a visual second channel. The first sketch lived inside the app; after [a post arguing for a standard](https://gbks.substack.com/p/unique-address-patterns), it became its own thing — open spec, two reference implementations, a site. Arké is in TestFlight if you'd like to see Hallmarks in real use.

— Christoph Ono
