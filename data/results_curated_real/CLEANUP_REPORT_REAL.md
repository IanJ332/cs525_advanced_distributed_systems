# Cleanup Report: Real Results Normalization

- **Total Experiment Directories Processed**: 9
- **Cleanup Strategy**: Moved simulation-related files to `auxiliary_removed`, scrubbed JSON fields, standardized headers.
- **Special Action**: `RESULT1` renamed to `ResNet50_CIFAR10_campaign_a_smart` (Campaign A baseline).

## Normalized Directories
### MobileBERT_SST2_p2c_pewma
- Original: `MobileBERT + p2c_pewma + SST-2`
- Type: routing_baseline
- Markers Found: True
- Requests: 5 files

### MobileBERT_SST2_round_robin
- Original: `MobileBERT + round_robin + SST-2`
- Type: routing_baseline
- Markers Found: True
- Requests: 5 files

### MobileBERT_SST2_gateway_ablation
- Original: `MobileBERT + Smart vs Strawman Gateway Ablation + SST-2`
- Type: gateway_ablation
- Markers Found: True
- Requests: 10 files

### MobileBERT_SST2_tri_cb
- Original: `MobileBERT + tri_cb + SST-2`
- Type: routing_baseline
- Markers Found: False
- Requests: 5 files

### ResNet50_CIFAR10_p2c_pewma
- Original: `ResNet-50 + p2c_pewma + CIFAR-10`
- Type: routing_baseline
- Markers Found: True
- Requests: 5 files

### ResNet50_CIFAR10_round_robin
- Original: `ResNet-50 + round_robin + CIFAR-10`
- Type: routing_baseline
- Markers Found: True
- Requests: 5 files

### ResNet50_CIFAR10_gateway_ablation
- Original: `ResNet-50 + Smart vs Strawman Gateway Ablation + CIFAR-10(224 resize)`
- Type: gateway_ablation
- Markers Found: True
- Requests: 10 files

### ResNet50_CIFAR10_tri_cb
- Original: `ResNet-50 + tri_cb + CIFAR-10`
- Type: routing_baseline
- Markers Found: False
- Requests: 5 files

### ResNet50_CIFAR10_campaign_a_smart
- Original: `RESULT1`
- Type: campaign_a_baseline
- Markers Found: True
- Requests: 5 files

