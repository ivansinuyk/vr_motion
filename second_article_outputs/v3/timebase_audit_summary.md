# Article 2 time-base audit

- Sessions audited: 25.
- Decoded videos with variable presentation intervals: 12/25.
- Sessions with unequal decoded-video and landmark frame counts: 1/25.
- Maximum absolute annotation-time versus decoded-PTS discrepancy: 19.620 ms.
- Maximum absolute landmark-time versus decoded-PTS grid discrepancy over shared frames: 66.745 ms.

## Event-frame comparisons

- transition proxy vs manual top: median absolute error 38.0 frames (session bootstrap 95% CI 29.0-98.0); median signed error -38.0 frames.
- transition proxy vs manual downswing transition: median absolute error 40.0 frames (session bootstrap 95% CI 33.0-112.0); median signed error -40.0 frames.
- impact detector vs manual impact: median absolute error 40.0 frames (session bootstrap 95% CI 34.0-51.0); median signed error -40.0 frames.

## Diagnostic examples

- smallest observed error: session `eb859af6-2991-42e4-9345-05d3baf63c6e`, transition proxy vs manual downswing transition, manual frame 172, automatic frame 186, signed error 14 frames.
- typical error: session `7473617c-26a8-428f-9ba6-fc51dd7d2156`, transition proxy vs manual top, manual frame 40, automatic frame 1, signed error -39 frames.
- largest observed error: session `81681211-21c8-4d55-9d89-095b3a80d022`, impact detector vs manual impact, manual frame 532, automatic frame 1, signed error -531 frames.

The top-of-backswing and downswing-transition rows are definition comparisons against one shared automatic transition output; they are not independent event detectors.
