This example demonstrates distributed averaging using Gustavo, Scarlet Mapper, and Redis.

Choose one:

- static-worker-average:
reads local CSV once and calculates once after membership stabilizes.

- dynamic-worker-average: 
continuously monitors local CSV and active worker membership, recalculating when data or nodes change.