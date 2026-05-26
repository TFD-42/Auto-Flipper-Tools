# Usage Guide

Detailed usage examples and workflows.

## Basic Usage

### Simple Classification

```bash
python Bad_USB_Classifier/classify_badusb.py /path/to/payloads
```

### Output

```
classified_badusb/
├── exfiltration/
│   ├── payload1.txt
│   └── payload2.duck
├── phishing/
│   └── phish_attack.txt
├── credentials/
├── remote_access/
└── unassigned/
    └── unknown_script.txt

classification.log  # Detailed log file
```

## Logging

### View Logs

```bash
# Real-time monitoring
tail -f classified_badusb/classification.log

# Full log
cat classified_badusb/classification.log

# Filter by level
grep "ERROR" classified_badusb/classification.log
grep "INFO" classified_badusb/classification.log
```

### Log Format

```
2024-01-15 10:30:45,123 - INFO - Moved payload1.txt -> exfiltration/
2024-01-15 10:30:46,456 - DEBUG - Found topic 'phishing' via keyword match
2024-01-15 10:30:47,789 - ERROR - Cannot read corrupted_file.txt: [Errno 2]
```

## Advanced Usage

### Batch Processing Multiple Directories

```bash
# Process multiple sources into single output
for dir in payload_source1 payload_source2 payload_source3; do
    python Bad_USB_Classifier/classify_badusb.py "$dir"
done
```

### Custom Output Location

```bash
# Modify script to change output path
# Edit classify_badusb.py line ~131
# output_root = /custom/output/path
```

### Integration with Workflows

#### 1. Flipper Zero Device Sync

```bash
# Classify payloads
python Bad_USB_Classifier/classify_badusb.py ~/flipper_payloads

# Copy to Flipper SD card
cp -r ~/flipper_payloads/classified_badusb/* \
    /Volumes/FLIPPER/badusb/
```

#### 2. Security Research Pipeline

```bash
#!/bin/bash
# Process, analyze, and archive

INPUT_DIR="$1"
OUTPUT_DIR="${INPUT_DIR}/analysis_results"

# Create output
mkdir -p "$OUTPUT_DIR"

# Classify
python Bad_USB_Classifier/classify_badusb.py "$INPUT_DIR"

# Copy results
cp -r "${INPUT_DIR}/classified_badusb" "$OUTPUT_DIR"

# Archive
tar -czf "${OUTPUT_DIR}/analysis_$(date +%Y%m%d).tar.gz" \
    "$OUTPUT_DIR/classified_badusb"

echo "Analysis complete: $OUTPUT_DIR"
```

#### 3. CI/CD Integration

```yaml
# Example: GitLab CI
classify_badusb:
  stage: analysis
  script:
    - python Bad_USB_Classifier/classify_badusb.py ./payloads
  artifacts:
    paths:
      - classified_badusb/
    reports:
      dotenv: .env
```

## Configuration

### Modifying Categories

Edit `classify_badusb.py`:

```python
TOPICS = [
    "exfiltration",
    "your_custom_category",  # Add custom topic
    "phishing",
    # ... more topics
]
```

### Changing Model

```python
OLLAMA_MODEL = "llama2:7b"  # Change AI model
```

Available models: https://ollama.ai/library

### File Extensions

```python
SUPPORTED_EXTENSIONS = {".txt", ".duck", ".ds", ".payload"}
```

### Performance Tuning

```python
# Reduce AI processing timeout for faster completion
timeout=15  # Reduced from 30 seconds
```

## Performance Optimization

### For Large Batches (1000+ files)

```bash
# Monitor progress
watch 'ls -la classified_badusb/*/ | wc -l'

# Process in parallel (Linux/macOS)
parallel python Bad_USB_Classifier/classify_badusb.py \
    ::: ./batch1 ./batch2 ./batch3
```

### Memory Usage

- Pattern detection: ~20MB
- AI classification: +50MB
- Total baseline: ~70MB

## Examples

### Example 1: Security Assessment

```bash
# Collect all BadUSB samples
find ~/research -name "*.duck" -o -name "*.txt" | wc -l

# Classify for analysis
python Bad_USB_Classifier/classify_badusb.py ~/research

# Generate report
cat classified_badusb/classification.log | grep "^2024"
```

### Example 2: Payload Organization

```bash
# Organize for presentation
python Bad_USB_Classifier/classify_badusb.py ~/payloads

# Create summary
echo "=== Payload Classification Summary ===" > SUMMARY.md
echo "Exfiltration: $(ls classified_badusb/exfiltration | wc -l)" >> SUMMARY.md
echo "Phishing: $(ls classified_badusb/phishing | wc -l)" >> SUMMARY.md
```

### Example 3: Continuous Monitoring

```bash
# Monitor new payloads
while true; do
    python Bad_USB_Classifier/classify_badusb.py ./incoming
    sleep 300  # Check every 5 minutes
done
```

## Troubleshooting

### Slow Performance

**Symptom**: Classification taking >2 minutes per file

**Solutions**:
1. Disable Ollama (uses pattern matching only)
2. Increase timeout value
3. Use faster computer
4. Reduce file size limit

### Memory Issues

**Symptom**: Out of memory errors

**Solutions**:
1. Process smaller batches
2. Close other applications
3. Increase swap space
4. Use lighter AI model

### File Not Moving

**Symptom**: Files remain in original location

**Solutions**:
1. Check file permissions
2. Ensure write access to output directory
3. Check disk space
4. Review error logs

## Best Practices

1. **Always backup** original files before processing
2. **Review logs** for processing issues
3. **Test with small batch** before large operations
4. **Monitor disk space** during batch processing
5. **Document custom categories** in CONTRIBUTING.md
6. **Regular updates** for security and features

## Next Steps

- Read [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- Check [../README.md](../README.md) for feature overview
- Review [../CONTRIBUTING.md](../CONTRIBUTING.md) for contributions
