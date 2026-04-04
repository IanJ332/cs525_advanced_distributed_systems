# Midterm Report Final Figure Audit & Notes

This file contains automated audit results for all generated figures to assist in report selection.

## MobileBERT_SST2_gateway_ablation
- **Input Files**: campaign_nlp_mobilebert_gatewaysmart_c128.csv, campaign_nlp_mobilebert_gatewaysmart_c32.csv, campaign_nlp_mobilebert_gatewaysmart_c48.csv...
- **Timeline Focus**: Concurrency 128 (selected based on knee-point max-derivative)
- **Peak Behavior**: P99 reached 180.0s, occurring in the **fault** phase
- **Fault Characterization**: Standard recovery observed
- **Placement Recommendation**: CORE TEXT
- **Special Notes**: Primary routing evaluation
## MobileBERT_SST2_p2c_pewma
- **Input Files**: campaign_nlp_mobilebert_p2c_c128.csv, campaign_nlp_mobilebert_p2c_c32.csv, campaign_nlp_mobilebert_p2c_c48.csv...
- **Timeline Focus**: Concurrency 128 (selected based on knee-point max-derivative)
- **Peak Behavior**: P99 reached 141.8s, occurring in the **fault** phase
- **Fault Characterization**: Standard recovery observed
- **Placement Recommendation**: CORE TEXT
- **Special Notes**: Primary routing evaluation
## MobileBERT_SST2_round_robin
- **Input Files**: campaign_nlp_mobilebert_rr_c128.csv, campaign_nlp_mobilebert_rr_c32.csv, campaign_nlp_mobilebert_rr_c48.csv...
- **Timeline Focus**: Concurrency 96 (selected based on knee-point max-derivative)
- **Peak Behavior**: P99 reached 146.6s, occurring in the **fault** phase
- **Fault Characterization**: Standard recovery observed
- **Placement Recommendation**: CORE TEXT
- **Special Notes**: Primary routing evaluation
## MobileBERT_SST2_tri_cb
- **Input Files**: campaign_nlp_mobilebert_tricb_c128.csv, campaign_nlp_mobilebert_tricb_c32.csv, campaign_nlp_mobilebert_tricb_c48.csv...
- **Timeline Focus**: Concurrency 96 (selected based on knee-point max-derivative)
- **Peak Behavior**: P99 reached 171.1s, occurring in the **fault** phase
- **Fault Characterization**: Standard recovery observed
- **Placement Recommendation**: CORE TEXT
- **Special Notes**: Primary routing evaluation
## ResNet50_CIFAR10_campaign_a_smart
- **Input Files**: campaign_a_cv_c16.csv, campaign_a_cv_c24.csv, campaign_a_cv_c32.csv...
- **Timeline Focus**: Concurrency 48 (selected based on knee-point max-derivative)
- **Peak Behavior**: P99 reached 107.2s, occurring in the **fault** phase
- **Fault Characterization**: Standard recovery observed
- **Placement Recommendation**: APPENDIX
- **Special Notes**: Campaign A baseline variant
## ResNet50_CIFAR10_gateway_ablation
- **Input Files**: campaign_cv_resnet_gatewaysmart_c16.csv, campaign_cv_resnet_gatewaysmart_c24.csv, campaign_cv_resnet_gatewaysmart_c32.csv...
- **Timeline Focus**: Concurrency 64 (selected based on knee-point max-derivative)
- **Peak Behavior**: P99 reached 164.2s, occurring in the **fault** phase
- **Fault Characterization**: Standard recovery observed
- **Placement Recommendation**: CORE TEXT
- **Special Notes**: Primary routing evaluation
## ResNet50_CIFAR10_p2c_pewma
- **Input Files**: campaign_cv_resnet_p2c_c16.csv, campaign_cv_resnet_p2c_c24.csv, campaign_cv_resnet_p2c_c32.csv...
- **Timeline Focus**: Concurrency 64 (selected based on knee-point max-derivative)
- **Peak Behavior**: P99 reached 150.1s, occurring in the **fault** phase
- **Fault Characterization**: Standard recovery observed
- **Placement Recommendation**: CORE TEXT
- **Special Notes**: Primary routing evaluation
## ResNet50_CIFAR10_round_robin
- **Input Files**: campaign_cv_resnet_rr_c16.csv, campaign_cv_resnet_rr_c24.csv, campaign_cv_resnet_rr_c32.csv...
- **Timeline Focus**: Concurrency 48 (selected based on knee-point max-derivative)
- **Peak Behavior**: P99 reached 92.7s, occurring in the **fault** phase
- **Fault Characterization**: Standard recovery observed
- **Placement Recommendation**: CORE TEXT
- **Special Notes**: Primary routing evaluation
## ResNet50_CIFAR10_tri_cb
- **Input Files**: campaign_cv_resnet_tricb_c16.csv, campaign_cv_resnet_tricb_c24.csv, campaign_cv_resnet_tricb_c32.csv...
- **Timeline Focus**: Concurrency 48 (selected based on knee-point max-derivative)
- **Peak Behavior**: P99 reached 99.2s, occurring in the **fault** phase
- **Fault Characterization**: Standard recovery observed
- **Placement Recommendation**: CORE TEXT
- **Special Notes**: Primary routing evaluation
