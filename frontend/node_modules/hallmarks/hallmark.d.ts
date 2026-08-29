export type HallmarkStyle = "standard" | "high-contrast" | "monochrome";
export interface HallmarkOptions {
    /** Visual style. Defaults to "standard". */
    style?: HallmarkStyle;
    /** Draw a 1-unit border in the primary color. Defaults to false. */
    bordered?: boolean;
}
export interface OklchColor {
    /** OKLCH lightness, 0..1 */
    L: number;
    /** OKLCH chroma, typically 0..0.4 */
    C: number;
    /** OKLCH hue, 0..360 (degrees) */
    h: number;
    /** sRGB hex string, e.g. "#7fa3c9" */
    hex: string;
}
export interface HallmarkSpec {
    /** 7-row × 5-col grid. 0 = background, 1 = primary, 2 = accent. */
    cells: number[][];
    background: OklchColor;
    primary: OklchColor;
    accent: OklchColor;
    /** Three BIP-39 words (the verbal companion). */
    words: [string, string, string];
    /** Single-string form, space-separated. */
    wordsText: string;
    style: HallmarkStyle;
    bordered: boolean;
}
declare function sha256(bytes: Uint8Array): Uint8Array;
interface PrngState {
    v: number;
}
declare function mulberry32Init(bytes: Uint8Array, offset: number): PrngState;
declare function mulberry32Next(state: PrngState): number;
declare function oklchToRgb(L: number, C: number, h: number): [number, number, number];
declare function generatePattern(bytes: Uint8Array): number[][];
declare function deriveColors(bytes: Uint8Array, style: HallmarkStyle): {
    bg: OklchColor;
    fg: OklchColor;
    ac: OklchColor;
};
declare function deriveWords(bytes: Uint8Array): [string, string, string];
export declare function hallmarkSpec(input: string, opts?: HallmarkOptions): HallmarkSpec;
export declare function hallmarkWords(input: string): [string, string, string];
/**
 * A 14×20 raster plus the per-style colors needed to paint it.
 * Pixel values: 0 = off, 1 = primary cell, 2 = accent cell (see SPEC §3.8).
 * The pixel grid is style-independent; only `colors` changes with style.
 */
export interface HallmarkPixelGrid {
    width: 14;
    height: 20;
    /** 14×20 = 280 values, row-major. Each value is 0, 1, or 2. */
    pixels: Uint8Array;
    /** Resolved per the selected style (default: "standard"). */
    colors: {
        background: OklchColor;
        primary: OklchColor;
        accent: OklchColor;
    };
    style: HallmarkStyle;
}
/**
 * Returns the 14×20 pixel grid for the input. Pixel values encode the cell
 * type (0 = off, 1 = primary, 2 = accent) so renderers can paint each pixel
 * appropriately for the selected style.
 *
 * The pixel layout is style-independent — every style emits the same grid.
 * The `style` option only affects the returned `colors`. For monochrome
 * rendering, treat values 1 and 2 identically; the diagonal pattern of
 * accent cells carries the value-2 distinction through shape alone.
 *
 * See SPEC §3.8.
 */
export declare function hallmarkPixels(input: string, opts?: HallmarkOptions): HallmarkPixelGrid;
/**
 * Builds an SVG string. Useful for SSR or when no DOM is available.
 * The viewBox is "0 0 100 132" — apply width/height via CSS or attributes.
 */
export declare function hallmarkSVG(input: string, opts?: HallmarkOptions): string;
/**
 * Builds an SVGSVGElement. Requires a DOM (browser or jsdom).
 */
export declare function hallmark(input: string, opts?: HallmarkOptions): SVGSVGElement;
/**
 * The aspect ratio of a hallmark tile, width : height.
 * Equal to 100 : 132 (1 : 1.32).
 */
export declare const HALLMARK_ASPECT: number;
export declare const HALLMARK_VIEWBOX: {
    width: number;
    height: number;
};
export declare const _internals: {
    sha256: typeof sha256;
    mulberry32Init: typeof mulberry32Init;
    mulberry32Next: typeof mulberry32Next;
    oklchToRgb: typeof oklchToRgb;
    generatePattern: typeof generatePattern;
    deriveColors: typeof deriveColors;
    deriveWords: typeof deriveWords;
};
export {};
