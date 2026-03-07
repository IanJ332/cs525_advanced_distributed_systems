# GrayPulse Container Image Versions (Freeze)

All related services use fixed **Image Digests** instead of tags to prevent version drift.

| Component | Registry | Image Digest |
|---|---|---|
| HAProxy (Ingress) | docker.io/library/haproxy:2.8 | `sha256:d8c11cd98c25dbfac5db81d6830cc106c5aa91ce9150aa84d0b28ecda9c148ca` |
| Triton Inference Server | nvcr.io/nvidia/tritonserver | `sha256:2f56708b5f375c3db77950bd16ec2272a0886a1df0f00f07cbaedec701eebb0b` |
| Prometheus | docker.io/prom/prometheus | `sha256:1a840eab71eef64121e73dbcc06e2327599723ecdbf56ceb9ba49d71c8936999` |
| Grafana | docker.io/grafana/grafana | `sha256:7cbbcd6e9cecccbc92dd1fb1b8e11e3b52d919aed5dcf6fd0aff405defc69999` |

> *Note: The Image Digests above are fixed example values. If you update to a newer image, run `docker inspect --format='{{index .RepoDigests 0}}' <image>` after `docker pull` to obtain and update the record.*

## Kernel and Sysctl Snapshot
Captured via `freeze_sysctl.sh`:
```ini
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_tw_reuse = 1
vm.swappiness = 10
kernel.pid_max = 655360
```
