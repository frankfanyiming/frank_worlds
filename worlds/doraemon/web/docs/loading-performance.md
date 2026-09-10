# Town loading — 2026-09-10

The initial town scene no longer waits for the original detailed bedroom. The town becomes ready only after its first rendered frame; 1.5 seconds later it starts preparing the complete bedroom in the background. Entering through navigation, the floor switch, the arbitrary door or the stairs waits for the finished room. Cancelling or choosing another destination prevents a delayed teleport. A bedroom error can be retried without restarting the town.

Versioned model, map and texture responses are saved in browser Cache Storage. Later visits read those bytes directly when available. Cache failures fall back to normal network loading. Failed HTTP responses are not cached; failed model/image decoding and invalid metadata evict the affected entry. This is an asset cache, not an offline application shell. The browser still decodes cached models/images and may clear storage.

Measured file sizes, including the actual 28 material maps selected by the restored room:

| Before the first town frame | Bytes |
| --- | ---: |
| Previous blocking scene assets | 273,293,451 |
| Current startup models and world data | 28,596,910 |
| Deferred original bedroom model | 48,063,076 |
| Deferred requested bedroom maps and manifest | 196,633,465 |

This removes 89.5% of scene asset bytes from the first-frame dependency chain. It does not claim an equivalent wall-clock speedup or reduce total first-visit downloads. Original GLB files, texture pixels/resolution, material assignments, shaders and lighting parameters are preserved.

Run `npm test`, `npm run typecheck`, `node tools/verify-adventure.cjs` and `npm run build:pages`. `tests/loading.test.cjs` exercises the real loading/material-selection/navigation code with network payload, WebGL and image-decoder fixtures; its output is `.test-build/loading-report.json`. It covers cache hits, version changes, offline cache reads, quota/private-mode fallback, abort, corrupt metadata recovery, deferred startup, atomic room attachment, staircase waiting, cancelled navigation, repeated entry and retry. These are integration checks, not real-browser loading-time or visual measurements.

`ASSET_VERSION` in `lib/town/model-manifest.ts` identifies immutable asset bytes. Keep it unchanged for code-only releases, including this release. Change it when model, world data, manifest or texture bytes change so clients cannot combine old cached assets with new content. The build keeps both startup and deferred models in the published output and reports their sizes separately in `asset-sizes.json`.
