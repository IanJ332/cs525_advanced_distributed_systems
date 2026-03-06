#!/bin/bash
# 自动备份实验证据（含 1s resolution 数据）至 archive/ 目录

WORKSPACE="/Users/ian/Desktop/cs525_advanced_distributed_systems"
SRC_DIR="${WORKSPACE}/20260306_motivation_test"
ARCHIVE_DIR="${WORKSPACE}/archive/20260306_motivation_test"

echo "1. Creating archive directory: ${ARCHIVE_DIR}"
mkdir -p "${ARCHIVE_DIR}"

echo "2. Exporting evidence summary log and raw requests (1s resolution included)..."
cp "${SRC_DIR}/evidence_summary.log" "${ARCHIVE_DIR}/"
cp "${SRC_DIR}/raw_requests.csv" "${ARCHIVE_DIR}/"
cp "${SRC_DIR}/raw_requests_1s_resolution.csv" "${ARCHIVE_DIR}/"

echo "3. Exporting linked versions snapshot for reproducibility..."
cp "${SRC_DIR}/versions_snapshot.md" "${ARCHIVE_DIR}/"
cp "${WORKSPACE}/VERSIONS.md" "${ARCHIVE_DIR}/"

echo "✅ High-resolution Evidence export complete! Core files saved to ${ARCHIVE_DIR}."
ls -lh "${ARCHIVE_DIR}"
