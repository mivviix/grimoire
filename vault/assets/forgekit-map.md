---
summary: Which forgekit tool makes which asset, and what each is bad at; read first for any asset task, then forgekit help <tool>
tags: forgekit, assets, pipeline, sound, vfx, mesh, animation, ui, icons
---
# forgekit: which tool for which asset

forgekit is the asset toolkit; its manuals are the truth for flags and formats (`forgekit help <tool>`, several names at once). This page is only the map and the lessons from using it.

| Need | Tool |
|---|---|
| Character animation (R15) | `forgekit animate` |
| 3D prop or model | `forgekit mesh` (Python model → .glb) |
| Buildings, scenery | `forgekit build` |
| Tiling material (brick, wood…) | `forgekit texture` |
| Particle effect | `forgekit vfx` |
| Game UI screens | `forgekit ui` |
| UI icons | `forgekit icon` |
| Store icon, thumbnails, concept art | `forgekit generate image` |
| Cutscene | `forgekit movie` |
| Ambience, longer sound | `forgekit sound` |
| Coin, click, hover, UI and pickup sounds | `forgekit sfx` (synth) |
| Music | `forgekit music` |
| Picture of the open place | `forgekit capture` |
| Put files into Studio | `forgekit import` |
| A whole game's assets and look | `forgekit help pipeline` |

## Lessons
- Short punchy combat sounds (hits, swings, gunshots) from `sound` or `sfx` were judged unusable in game: say so up front and suggest recorded library sounds the user edits.
- Check assets with forgekit's own previews and numbers, not Studio screenshots.
- `forgekit setup` once per place before importing VFX, animations or movies: it installs the modules game scripts require.
