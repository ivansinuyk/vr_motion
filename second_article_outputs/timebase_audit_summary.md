# Article 2 time-base audit

- Sessions audited: 25.
- Decoded videos with variable presentation intervals: 12/25.
- Sessions with unequal decoded-video and landmark frame counts: 1/25.
- Maximum absolute annotation-time versus decoded-PTS discrepancy: 19.620 ms.
- Maximum absolute landmark-time versus decoded-PTS grid discrepancy over shared frames: 66.745 ms.

## Event-frame comparisons

- transition proxy vs manual top: median absolute error 43.0 frames (session bootstrap 95% CI 36.0-110.0); median signed error -43.0 frames.
- transition proxy vs manual downswing transition: median absolute error 46.0 frames (session bootstrap 95% CI 39.0-114.0); median signed error -46.0 frames.
- impact detector vs manual impact: median absolute error 42.0 frames (session bootstrap 95% CI 33.0-52.0); median signed error -42.0 frames.

## Diagnostic examples

- smallest observed error: session `eb859af6-2991-42e4-9345-05d3baf63c6e`, impact detector vs manual impact, manual frame 242, automatic frame 228, signed error -14 frames.
- typical error: session `42f8729a-ed28-45a2-bf9b-397d2d698bb0`, impact detector vs manual impact, manual frame 58, automatic frame 15, signed error -43 frames.
- largest observed error: session `81681211-21c8-4d55-9d89-095b3a80d022`, impact detector vs manual impact, manual frame 535, automatic frame 1, signed error -534 frames.

The top-of-backswing and downswing-transition rows are definition comparisons against one shared automatic transition output; they are not independent event detectors.
