# Scientific Questions (GrayPulse)

The experimental design and data sampling of this project aim to answer and validate the following core Research Questions (RQs):

## RQ1: Detection Signals
**Question**: Compared to low-level hardware monitors and gateway error rates, can end-to-end latency and queuing behavior capture "Gray Failures" earlier and more accurately?
*   **Hypothesis (H1)**: Fine-grained application-layer signals (Queue Depth and P99 Latency) can flag local response degradation (Gray Failure) caused by resource contention earlier and more accurately than heartbeats. Low-level hardware metrics (like GPU utilization or error logs) exhibit significant blind spots and delays in such failures.

## RQ2: Root Cause Differentiation
**Question**: Can the gray-scale detection algorithm accurately distinguish between global high load (traffic spikes) and local node degradation (actual failures)?
*   **Hypothesis (H2)**: The Robust Z-score algorithm, utilizing sliding window medians and Median Absolute Deviation (MAD), can self-suppress during normal global traffic fluctuations, isolating and capturing only local distribution extremes specific to individual node behavior.

## RQ3: Mitigation Overhead
**Question**: Can a routing isolation strategy (Z-score based draining) achieve lower overhead than "Request Hedging," commonly used in microservice architectures?
*   **Hypothesis (H3)**: When a node experiences a gray-scale slowdown, employing soft-draining can immediately restore cluster P99 latency with negligible overhead. In contrast, Hedging introduces significant secondary CPU and internal network traffic overhead, potentially inducing cascading failures due to resource exhaustion.
