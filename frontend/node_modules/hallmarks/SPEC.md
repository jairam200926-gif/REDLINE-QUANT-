# Hallmarks Specification

**Version:** 1.0
**Status:** Draft
**Date:** 2026-05-13
**License:** CC0 1.0 Universal (public domain)

---

## Abstract

Hallmarks are deterministic visual marks derived from any string identifier, designed to make it possible to confirm at a glance that two identifiers are the same — without having to read them character by character. Each input produces a distinct 5×7 symmetric pattern of colored dots, a three-word verbal companion drawn from the BIP-39 English wordlist, and an optional 14×20 pixel-art rendering for low-resolution displays. All three representations are derived from a single SHA-256 hash of the input, so any two implementations of this specification produce byte-identical output for the same input.

---

## 1. Motivation

People are bad at comparing long opaque strings character by character. Crypto addresses, SSH key fingerprints, commit SHAs, container digests, API keys, content hashes — anything you'd otherwise display as forty or more random characters — invite the same failure mode: the eye skims, the mind fills in, and a transposed character slips through.

Hallmarks exist for that comparison job. They are not avatars and they are not memory aids. The reader does not need to remember what last week's hallmark looked like; they only need to compare what is on the screen with what is somewhere else — another screen, a printed receipt, a hardware wallet display, a teammate's terminal. If the two hallmarks match, the strings match. If they differ, even by one character of input, the hallmarks differ dramatically, because SHA-256's avalanche property guarantees that changing one bit of input flips roughly half the bits of the hash.

This specification covers three coordinated output forms:

- A **visual pattern**: a small, colored, left-right-symmetric grid suitable for in-line display next to an address or identifier.
- A **verbal companion**: three BIP-39 words that act as a screen-reader-friendly, voice-comparable, plain-text representation of the same hash.
- A **low-resolution variant**: an exact 14×20 pixel grid for hardware wallets, e-ink readers, embedded UIs, and any display where sub-pixel rendering is not available.

The visual and the verbal are designed to be used together: the visual provides instant comparison, the verbal provides an accessible fallback and a voice-friendly channel. Implementations are encouraged to expose both.

---

## 2. Terminology

| Term | Meaning |
|---|---|
| **Input** | A UTF-8 string. Conventionally an address, key, hash, or other identifier, but the algorithm makes no assumptions about content. |
| **Hash** | The SHA-256 digest of the UTF-8 bytes of the input. Exactly 32 bytes. |
| **Cell** | One of the 35 positions in the 5-column × 7-row grid. Each cell has a value of 0 (background), 1 (primary), or 2 (accent). |
| **Half-grid** | The left three columns of the grid (15 cells in 7 rows × 3 columns), generated independently, then mirrored to produce the full 5-column grid. |
| **Pattern** | The complete 5×7 grid of cell values. |
| **Fill ratio** | The proportion of non-zero cells in the half-grid, used to enforce visual density. |
| **Style** | One of `standard`, `high-contrast`, or `monochrome`; selects the OKLCH color parameters and (for monochrome) the rendering technique for the accent value. |
| **Verbal companion** | A three-word string derived from the hash using the BIP-39 English wordlist. |
| **Low-res rendering** | The exact 14×20 pixel raster representation of the pattern. |

All bit and byte indices in this specification are zero-based. All byte orderings are big-endian unless explicitly stated.

---

## 3. Algorithm

### 3.1 Input encoding and hashing

The input MUST be encoded as UTF-8. No leading or trailing whitespace is stripped; no case normalization is applied. The input bytes are hashed with SHA-256 to produce a 32-byte digest, referred to below as `bytes[0..32]`.

```
bytes[0..32] = SHA-256( UTF-8( input ) )
```

The remainder of the algorithm consumes specific byte ranges from this digest:

| Bytes | Used for |
|---|---|
| 0..1 | Primary hue |
| 2..3 | Accent hue offset |
| 4..27 | Pattern generation (Mulberry32 seed, cycled across attempts) |
| 27..31 | Verbal companion (low 33 bits of these 5 bytes) |

The pattern attempt windows and the verbal companion both touch byte 27. In practice the pattern almost always succeeds at attempt 0 (which uses bytes 4..7), so the overlap with the verbal companion is benign. See §3.5 for the full re-seed schedule.

### 3.2 Color derivation

Two hues are derived: a **primary hue** (`h1`) and an **accent hue** (`h2`).

```
h1 = ((bytes[0] << 8) | bytes[1]) / 65536 * 360            // degrees
offsetRaw = ((bytes[2] << 8) | bytes[3]) / 65536           // 0.0 .. 1.0
h2_offset = 100 + offsetRaw * 160                           // 100° .. 260°
h2 = (h1 + h2_offset) mod 360                               // degrees
```

The accent hue offset is constrained to the range [100°, 260°] so that the accent never falls in the same hue family as the primary. This guarantees a clearly distinguishable two-color palette across the entire input space.

The background, primary (foreground), and accent colors are produced by combining a hue with style-specific lightness (`L`) and chroma (`C`) values, as listed in §4. The resulting OKLCH triple is converted to sRGB using the procedure in §3.7.

The background and primary colors use `h1`; the accent color uses `h2`. For the `monochrome` style, both hues are set to 0° (chroma is 0 so the hue choice is irrelevant; specifying 0° makes implementations reproducible).

### 3.3 Pattern generation

The pattern is generated by filling the half-grid (7 rows × 3 columns = 21 cells) with values drawn from a deterministic pseudorandom number generator, then mirroring left-right to produce the full 5-column grid.

**PRNG.** The PRNG is **Mulberry32**, seeded from a 4-byte window of the hash. Mulberry32 is small, fast, and produces well-distributed 32-bit outputs. It is specified in §3.6.

**Half-grid filling.** For each of the 7 rows, and within each row for each of the 3 half-columns, draw one value `v ∈ [0, 1)` from the PRNG and assign a cell value:

```
if v < 0.50:        cell = 0   (background)
else if v < 0.85:   cell = 1   (primary)
else:               cell = 2   (accent)
```

This yields an expected distribution of 50% background, 35% primary, 15% accent.

**Mirroring.** For each row, the half-row `[a, b, c]` is mirrored to produce the full 5-column row `[a, b, c, b, a]`. Column 0 mirrors column 4; column 1 mirrors column 3; column 2 is the axis of symmetry and is not mirrored.

**Density check and re-seeding.** After generating all 7 rows, the implementation counts the number of non-zero cells in the half-grid (`filledCount`) and computes:

```
fillRatio = filledCount / 21
```

If `fillRatio` is outside the inclusive range [0.45, 0.75], the pattern is too sparse or too dense for reliable visual differentiation. The implementation discards the pattern and retries with a new PRNG seed taken from a different byte window of the hash.

**Re-seed schedule.** Attempt `n` (zero-indexed) seeds the PRNG from bytes starting at offset `(4 + n × 4) mod 28`. Up to 8 attempts are made:

| Attempt | Seed byte offset | Seed bytes |
|---|---|---|
| 0 | 4  | bytes[4..8]  |
| 1 | 8  | bytes[8..12] |
| 2 | 12 | bytes[12..16] |
| 3 | 16 | bytes[16..20] |
| 4 | 20 | bytes[20..24] |
| 5 | 24 | bytes[24..28] |
| 6 | 0  | bytes[0..4]  |
| 7 | 4  | bytes[4..8]  |

The first attempt whose `fillRatio` lands in [0.45, 0.75] is accepted. If no attempt succeeds (which occurs for far less than 0.01% of inputs in practice), the pattern from attempt 0 is used as a fallback.

### 3.4 Verbal companion

The verbal companion is three words drawn from the **BIP-39 English wordlist** (2048 words, indices 0..2047), space-separated.

Thirty-three bits are extracted from the low 33 bits of bytes 27..31:

```
v = ((bytes[27] & 0x7F) << 32)
  | (bytes[28] << 24)
  | (bytes[29] << 16)
  | (bytes[30] <<  8)
  |  bytes[31]
```

`v` is a 33-bit unsigned integer. The three word indices are extracted as 11-bit slices, most significant first:

```
i1 = (v >> 22) & 0x7FF
i2 = (v >> 11) & 0x7FF
i3 =  v        & 0x7FF

words = [ bip39[i1], bip39[i2], bip39[i3] ]
```

The canonical text form is the three words joined by single ASCII spaces:

```
"violin orbit tangerine"
```

The verbal companion is intended for:

- **Accessibility:** screen readers announce the three words in place of an image description.
- **Voice verification:** "Does your screen say *violin orbit tangerine*?"
- **Optional UI display:** rendered as a sub-caption beneath the visual.

### 3.5 Geometry and rendering (visual pattern)

The visual pattern is rendered as a rounded-rectangle tile with the cell grid inside.

**Tile dimensions.** Let `W` be the rendered width. Then:

```
padding       = 0.10 × W          // 10% of width, on all four edges
cellSize      = (W - 2 × padding) / 5
innerHeight   = cellSize × 7
H             = innerHeight + 2 × padding
```

The resulting aspect ratio is `W : H = 100 : 132` (the tile is taller than it is wide).

**Corner radius.**

```
cornerRadius = 0.16 × W
```

**Cell coordinates.** For cell at column `x` (0..4) and row `y` (0..6), the cell center is:

```
centerX = padding + x × cellSize + cellSize / 2
centerY = padding + y × cellSize + cellSize / 2
```

**Background.** The full tile is filled with the background color, with corners rounded to `cornerRadius`.

**Primary cells (value 1).** A filled circle of radius `0.40 × cellSize` (diameter = 80% of cell width), centered at the cell center, painted in the primary color.

**Accent cells (value 2).**

For `standard` and `high-contrast` styles: a filled circle of radius `0.46 × cellSize` (15% larger than primary cells), centered at the cell center, painted in the accent color.

For `monochrome` style: a filled rounded square of side `0.92 × cellSize` (i.e. `2 × 0.46 × cellSize`) with corner radius `0.15 × side`, centered at the cell center, painted in the accent color. The shape difference (circle vs. square) carries the primary/accent distinction in place of the size difference, because color is removed in monochrome.

**Border (optional).** If the bordered variant is requested, a 1-unit stroke is drawn along the inside of the rounded-rect tile, inset by 0.5 units, in the primary color. The stroke does not change the tile's outer dimensions. "1 unit" here means 1 unit of the renderer's coordinate space; for a tile rendered at 1.0 width, this corresponds to a hairline appropriate to the device pixel ratio.

### 3.6 Mulberry32

Mulberry32 is a small 32-bit PRNG. All arithmetic is performed modulo 2³². Bit operations are unsigned 32-bit.

**Seeding.** Given four bytes `b0, b1, b2, b3` from the hash, the initial 32-bit state is:

```
state = (b0 << 24) | (b1 << 16) | (b2 << 8) | b3
```

(That is, big-endian interpretation of the four bytes.)

**Next.** Each call to `next()` returns a `Double` in the half-open interval `[0, 1]` (the upper bound is inclusive in this spec's variant, by design — see note below) and advances the state:

```
state = (state + 0x6D2B79F5) mod 2^32
t     = state
t     = ((t XOR (t >>> 15)) × (t OR 1)) mod 2^32
t     = ((t + (((t XOR (t >>> 7)) × (t OR 61)) mod 2^32)) mod 2^32) XOR t
result = t XOR (t >>> 14)

next = result / (2^32 − 1)
```

**Note on the divisor.** This specification divides by `2³² − 1`, not `2³²`, matching the reference Swift implementation. The practical difference is a single `result == 0xFFFFFFFF` case that yields exactly `1.0` instead of slightly less; this never affects the threshold comparisons in §3.3 because the thresholds (`0.50`, `0.85`) are not representable as `k / (2³² − 1)` for any integer `k`. Implementations MUST divide by `2³² − 1` for byte-identical reproduction of the reference test vectors.

### 3.7 OKLCH to sRGB

Hallmark colors are specified in **OKLCH** — a perceptually uniform color space — and converted to sRGB for rendering. The conversion follows Björn Ottosson's published OKLab definition.

**OKLCH → OKLab.** Given `L`, `C`, `h` (degrees):

```
a = C × cos(h × π / 180)
b = C × sin(h × π / 180)
```

**OKLab → linear sRGB.**

```
l_ = L + 0.3963377774 × a + 0.2158037573 × b
m_ = L − 0.1055613458 × a − 0.0638541728 × b
s_ = L − 0.0894841775 × a − 1.2914855480 × b

l3 = l_³
m3 = m_³
s3 = s_³

rLin =  4.0767416621 × l3 − 3.3077115913 × m3 + 0.2309699292 × s3
gLin = −1.2684380046 × l3 + 2.6097574011 × m3 − 0.3413193965 × s3
bLin = −0.0041960863 × l3 − 0.7034186147 × m3 + 1.7076147010 × s3
```

**Linear sRGB → sRGB.** For each channel `v`, clamp to `[0, 1]` and apply the standard sRGB transfer function:

```
v' = 12.92 × v                          if v ≤ 0.0031308
v' = 1.055 × v^(1/2.4) − 0.055          otherwise
```

The clamp is required because the OKLCH values defined in §4 stay safely within the sRGB gamut for any hue, but rounding error in cube terms can produce slightly out-of-range values. Without the clamp, implementations may diverge in those edge cases.

### 3.8 Low-resolution rendering (14×20)

For displays where sub-pixel rendering is unavailable or visually noisy — hardware wallets such as SeedSigner, e-ink readers, embedded LCDs, monochrome OLEDs — Hallmarks provides an exact pixel grid.

**Dimensions.** The low-res rendering is exactly **14 pixels wide × 20 pixels tall**, with no outer padding:

```
width  = 5 cells × 2 px + 4 gaps × 1 px = 14 px
height = 7 cells × 2 px + 6 gaps × 1 px = 20 px
```

**Pixel layout.** Cell `(x, y)` occupies a 2×2 block at:

```
pixelX = x × 3      // (2 px cell + 1 px gap)
pixelY = y × 3
```

with the four pixels of the cell at `(pixelX, pixelY)`, `(pixelX+1, pixelY)`, `(pixelX, pixelY+1)`, `(pixelX+1, pixelY+1)`.

**Cell rendering.** For a cell with value `v`, the four pixels of its 2×2 block are written as follows:

| Cell value | Top-left | Top-right | Bottom-left | Bottom-right |
|---|---|---|---|---|
| 0 (background) | 0 | 0 | 0 | 0 |
| 1 (primary) | 1 | 1 | 1 | 1 |
| 2 (accent) | 2 | 0 | 0 | 2 |

That is, **each lit pixel carries the value of its source cell** (1 or 2), preserving the primary/accent distinction in the pixel grid itself. Off pixels are 0. Implementations MUST emit pixel grids using these three values; binary on/off output is **not** conformant.

The diagonal pattern for accent cells keeps the three-value distinction visible at native size — even without color — and renders as a tilted-square aesthetic when upscaled with nearest-neighbor.

**Pixel layout is style-independent.** The same pixel grid (positions and values) is emitted for `standard`, `high-contrast`, and `monochrome` styles. Style only affects how each pixel value is painted.

**Color application per style.**

| Pixel value | `standard` / `high-contrast` | `monochrome` |
|---|---|---|
| 0 | background color (§3.2) | background color (off) |
| 1 | primary color (§3.2) | primary color (on) |
| 2 | accent color (§3.2) | primary color (on) |

For the colored styles, the §3.2 OKLCH triple is resolved using the style's L/C values (§4). For `monochrome`, values 1 and 2 are painted in the *same* color; the diagonal pattern carries the value-2 distinction. Implementations rendering to physically monochrome displays (e-ink, single-color OLED) collapse 1 and 2 to "on" — the grid's shape is unaffected, only the paint.

**Upscaling.** The 14×20 grid SHOULD be upscaled with nearest-neighbor interpolation. Anti-aliased upscaling defeats the pixel-art aesthetic and reduces clarity at small target sizes.

---

## 4. Style variants

Three styles are defined. Each style specifies OKLCH lightness and chroma values for the three colors (background, primary, accent); the hues are derived per §3.2.

### 4.1 Standard

The default style. Soft tinted background, mid-lightness primary dots, slightly brighter accent dots.

| Color | L | C |
|---|---|---|
| Background | 0.96 | 0.025 |
| Primary | 0.52 | 0.16 |
| Accent | 0.66 | 0.18 |

### 4.2 High contrast

For environments where extra contrast is needed (sunlight, low-quality displays, vision impairment). Background near white, primary near black, accent very saturated.

| Color | L | C |
|---|---|---|
| Background | 0.98 | 0.04 |
| Primary | 0.28 | 0.32 |
| Accent | 0.15 | 0.40 |

### 4.3 Monochrome

Grayscale. Hue is set to 0°; chroma is 0. The primary/accent distinction is carried by shape (circle vs. rounded square) instead of color.

| Color | L | C |
|---|---|---|
| Background | 0.96 | 0.0 |
| Primary | 0.30 | 0.0 |
| Accent | 0.30 | 0.0 |

---

## 5. Accessibility

Hallmarks are designed to be usable by readers with a wide range of vision profiles.

- **Color vision deficiency.** The `monochrome` style is the supported fallback for color-blind users and accessibility-strict environments. It uses shape (circle vs. rounded square) instead of color to carry the value-2 distinction, preserving the three-value pattern entirely.
- **Low vision.** The `high-contrast` style boosts the lightness gap between background and primary from ~0.44 to ~0.70 and increases accent chroma.
- **Blind users.** The verbal companion (§3.4) is the primary mechanism. Implementations SHOULD use the three-word string as the `aria-label` (or platform-equivalent accessibility label) of the rendered hallmark, e.g.:
  ```
  <img aria-label="Hallmark: violin orbit tangerine" ...>
  ```
- **Voice verification.** The verbal companion is also the basis for spoken comparison ("Does your screen say *violin orbit tangerine*?"), useful in remote-support flows and hardware wallet confirmations.

Implementations SHOULD expose both the visual and the verbal companion, and SHOULD allow the user or host application to choose the style.

---

## 6. Security and collision analysis

Hallmarks are a **comparison aid**, not a cryptographic commitment. They reduce the cognitive cost of comparing two identifiers by mapping the comparison into a visual domain. A passing visual comparison does not prove that two strings are identical; only direct string comparison can prove that.

That said, the visual entropy is sufficient that accidental collisions are vanishingly rare in practical use.

### 6.1 Visual entropy

The pattern carries `3⁷ˣ³ = 3²¹ ≈ 1.05 × 10¹⁰` possible half-grid configurations. After mirroring, this is also the count of possible full patterns.

The color pair adds:

- Primary hue: 16 bits → 65 536 distinct hues.
- Accent offset: 16 bits mapped to a 160° range → effectively ~40 000 distinct accent placements per primary hue.
- Combined: ~2.6 × 10⁹ color pairs.

Total visual entropy (pattern × color):

```
1.05 × 10¹⁰  ×  2.6 × 10⁹  ≈  2.7 × 10¹⁹
```

That is approximately **64 bits** of visual entropy. With 10 million addresses in circulation, the probability of any two sharing the same hallmark is approximately 1 in 2.7 trillion.

For the `monochrome` style, color is removed and only the pattern entropy remains: `~1.05 × 10¹⁰`, or about **33 bits**. With 10 000 addresses, the collision probability is approximately 1 in 2 million — still adequate for the comparison use case.

### 6.2 Verbal entropy

Three BIP-39 words carry exactly **33 bits** of entropy (2048³ ≈ 8.6 × 10⁹). The verbal companion is intentionally lower-entropy than the visual; it is a secondary channel, not a replacement.

### 6.3 Combined entropy

When both the visual (colored) and the verbal companion are compared, the effective entropy is bounded by the underlying hash. Because both are derived from independent slices of the SHA-256 output, comparing both raises the effective comparison entropy to approximately **64 + 33 = 97 bits** in the best case, with significant overlap in practice. Implementations SHOULD treat the visual and verbal as complementary checks rather than independent ones.

### 6.4 What hallmarks do not protect against

- **Address poisoning where the attacker controls the address.** An attacker who can generate addresses can grind for one whose hallmark resembles a target's. The cost of grinding for a *visually similar* hallmark is much lower than for a colliding hash, because human vision tolerates imprecision. Hallmarks shrink the attack surface but do not close it.
- **Shoulder surfing.** A visible hallmark, like a visible address, can be photographed and matched to identify users across contexts.
- **Substitution at the source.** If the rendering pipeline is compromised, the attacker controls what hallmark is displayed.

Hallmarks reduce the rate of *accidental* errors (typos, copy-paste truncation, wrong-address-selected) far more than they affect *adversarial* ones.

---

## 7. Test vectors

The reference test vectors live in `test-vectors.json` and cover, for each input string:

- The SHA-256 hash (hex).
- The 5×7 cell grid (as a 7-row array of 5 integers each).
- The OKLCH triples for background, primary, and accent (under each style).
- The three verbal companion words.
- The 14×20 pixel grid (as a 20-row array of 14 integers each, where 0 = off, 1 = primary pixel, 2 = accent pixel).

An implementation conforms to this specification if and only if it reproduces every test vector exactly.

The reference inputs include common Bitcoin address forms (P2PKH, P2SH, bech32 segwit, bech32m taproot), Ark addresses, an SSH key fingerprint, a Git commit SHA-1, a UUID, a long random string, and an empty string, to exercise the full input range.

---

## 8. Implementation notes

### 8.1 Mulberry32 portability

The most common source of cross-implementation divergence is integer overflow handling in Mulberry32. Implementers MUST:

- Treat the state as **unsigned 32-bit**.
- Perform all arithmetic modulo 2³² (e.g. via `>>> 0` in JavaScript, `&*` and `&+` in Swift, `wrapping_*` in Rust, `numpy.uint32` or explicit masks in Python).
- Use the **unsigned right shift** for `>>` (logical, not arithmetic).
- Divide by `4 294 967 295` (`2³² − 1`), not `4 294 967 296`, to match the reference.

### 8.2 OKLCH gamut

The OKLCH values in §4 stay within the sRGB gamut for every hue. The clamp in §3.7 is a defensive safety net for floating-point error in the cube terms and matrix multiply; it should not change the output for any hue in [0°, 360°) under the L and C values specified. Implementations MAY skip the clamp for performance but MUST produce output indistinguishable from the clamped version at 8-bit channel depth.

### 8.3 SVG vs. raster output

The visual pattern is shape-based and renders identically as SVG or raster. Implementations targeting the web SHOULD output SVG to preserve sharpness at every zoom level. Implementations targeting fixed-resolution displays MAY rasterize.

The 14×20 low-res rendering is inherently raster.

### 8.4 Recommended rendering sizes

| Use case | Recommended size |
|---|---|
| Inline next to an address line | 22–34 px wide |
| Avatar in a contact list | 48–64 px wide |
| Confirmation modal hero | 96–128 px wide |
| Print, business card | 12–20 mm wide |
| Hardware wallet, e-ink | 14×20 px native, upscaled with nearest-neighbor |

At sizes below 22 px wide, the cells become smaller than typical pointer hit-targets and finer detail is lost; below 18 px, the low-res 14×20 variant is recommended instead.

### 8.5 Determinism

Conformant implementations are byte-deterministic: same input string in, same hallmark out, on every platform, for every release. This property is what makes Hallmarks usable for verification. Any change that breaks determinism is a breaking change and requires a new major version of this specification.

---

## 9. Versioning

This specification is **Hallmarks v1.0**. Future versions may add output forms (e.g. an animated variant, a higher-resolution mode) but MUST NOT change the byte-level output of any existing form for any existing input. Test vectors from v1.0 MUST continue to match in v1.x.

---

## 10. References

- Björn Ottosson, *A perceptual color space for image processing.* https://bottosson.github.io/posts/oklab/
- BIP-39, *Mnemonic code for generating deterministic keys.* https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki
- Mulberry32 PRNG. https://github.com/bryc/code/blob/master/jshash/PRNGs.md#mulberry32
- SHA-256, FIPS 180-4.
- "Awesome Identicons" (prior art catalog). https://github.com/drhus/awesome-identicons

---

*This specification is dedicated to the public domain under CC0 1.0. Implementations are free to use, modify, and distribute it without attribution, though attribution is appreciated.*
