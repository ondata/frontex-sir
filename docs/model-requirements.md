# Model Requirements for Frontex SIR Extraction

## Overview

This document describes the requirements and characteristics of AI models used for extracting structured data from Frontex Serious Incident Reports (SIR) PDFs.

## Supported Models

### Gemini 2.5 Flash (current default)

**Specs:**
- Context window: 1M tokens input, 65K output
- File upload: max 10MB (via File API)
- Temperature: 0-2 (default: 0 for deterministic extraction)
- Thinking: supported
- Structured output: `application/json`

**Pros:**
- Fast inference suitable for batch processing
- Good balance of accuracy and speed
- Low cost

**Cons:**
- May have lower accuracy on numeric extraction compared to Pro
- Can struggle with ambiguous phrasing

**Use case:** Default model for production batch processing.

---

### Gemini 2.5 Pro

**Specs:**
- Context window: 1M tokens input, 65K output
- File upload: max 10MB (via File API)
- Temperature: 0-2 (default: 0 for deterministic extraction)
- Thinking: supported
- Structured output: `application/json`

**Pros:**
- Higher accuracy on numeric extraction
- Better reasoning on ambiguous data
- Better understanding of complex PDF layouts

**Cons:**
- Slower inference
- Higher cost

**Use case:** A/B testing, high-value documents, or reprocessing failures.

---

### Alternative Models (for future testing)

#### Gemini 3 Flash Preview
- Context: 1M tokens
- Latest model with enhanced reasoning
- Experimental status

#### Gemma 3 27B
- Open model
- Context: 131K tokens (smaller)
- Can be self-hosted for privacy

## Cost Estimation

### Gemini 2.5 Flash
- Input: ~$0.075/1M tokens
- Output: ~$0.30/1M tokens
- Estimated per PDF: $0.004-0.012 (assuming 5-15K input tokens, 500-2K output tokens)

### Gemini 2.5 Pro
- Input: ~$0.50/1M tokens
- Output: ~$1.50/1M tokens
- Estimated per PDF: $0.03-0.06

**Note:** These are rough estimates based on general Gemini pricing. Check actual pricing at https://ai.google.dev/pricing

## Rate Limits

### Free Tier
- Limits vary and change frequently
- Not exposed via API
- Check https://aistudio.google.com/app/apikey for your account limits
- Generally generous for testing (hundreds of requests)

### Paid Tier
- Rate limits depend on billing plan
- Can use Provisioned Throughput for guaranteed capacity
- Batch API available for bulk processing

## Technical Requirements

### File Upload
- Max size: 10MB per file
- Supported formats: PDF only
- File remains uploaded for 48 hours (automatic cleanup needed)

### API Response
- Returns `usageMetadata.totalTokenCount` for tracking
- Should log for cost monitoring
- Response time: 2-10s per PDF (Flash), 5-20s (Pro)

### Error Handling
- 429 Too Many Requests: rate limit exceeded
- 400 Bad Request: invalid input or parameters
- 500 Server Error: temporary failure
- Timeout: no built-in timeout, needs client-side configuration

## Recommendations for Scaling

### Batch Processing (100+ PDFs)
1. **Use Flash for initial pass** - Process all PDFs with Flash
2. **Reprocess failures with Pro** - Higher accuracy on edge cases
3. **Implement parallelism** - 5-10 concurrent requests with proper rate limiting
4. **Add budget limits** - Stop after N requests or cost threshold
5. **Monitor usage** - Track tokens per PDF for cost optimization

### A/B Testing
- Process sample (10-20 PDFs) with both models
- Compare:
  - Extraction accuracy (manual review)
  - Confidence distribution
  - Processing time
  - Token usage
- Use prompt versioning (`prompts/extract_sir_v2.txt`) to test different prompts

### Error Recovery
- Implement exponential backoff for 429/5xx errors
- Store failed PDFs for reprocessing
- Log error types for analysis
- Consider alternative models for specific error patterns

## Future Improvements

### Model Selection Heuristics
```
If PDF size > 5MB → Use Pro (better OCR)
If confidence = "bassa" → Reprocess with Pro
If retry_count > 3 → Flag for manual review
```

### Cost Optimization
- Batch API for bulk uploads
- Context caching for repeated processing
- Prompt caching for multi-turn workflows

### Accuracy Improvements
- Few-shot examples in prompt
- Custom fine-tuning on labeled SIR data
- Multi-stage extraction (coarse → fine)

## Monitoring Metrics

Track these metrics in production:
- `total_requests`: Number of API calls
- `successful_requests`: Success rate
- `total_tokens_input`: Input token usage
- `total_tokens_output`: Output token usage
- `avg_confidence`: Mean confidence level
- `low_confidence_count`: Records with confidence="bassa"
- `processing_time_avg`: Average seconds per PDF
- `error_rate`: Percentage of failed requests
- `estimated_cost`: Total cost based on token usage

## Version History

- 2026-02-13: Initial version with Gemini 2.5 models
