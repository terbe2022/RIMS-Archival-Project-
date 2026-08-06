# Image Classification Project — Technical Documentation

This project classifies sensitive content in archival images using two methods:

- **Method 1 — Semantic Similarity-Based Classification:** Uses image descriptions (long and short) and a semantic similarity classifier against a taxonomy of labels and keywords.
- **Method 2 — LLM Prompt-Based Moderation Classification:** Uses an LLM (LLaVA) with a strict moderation prompt to assign a single category and a short rationale (or `null` if the image is not offensive).

---

## Prompts

### 1. Natural Description Prompt (Method 1)
> Only describe what you actually see in the image.
> Do not guess names, locations, or add context.
> If unsure, say 'unknown'.

---

### 2. Strict One-Sentence Prompt (Method 1)
> Summarize the image in one or two sentences.
> Output must be strict and factual, using only observable details.
> Do not explain, infer, or add context.

---

### 3. LLaVA Classification Prompt (Method 2)
```text
<image>{jpg_path}</image>

You are an image moderation classifier.
Determine if the image contains any hate symbols or offensive/insensitive content.
If yes, assign it to ONE of these categories:
{categories_list}

If not offensive, set category and rationale to null.

Output format (strict JSON only):
{"offensive": true/false, "category": "category_name_or_null", "rationale": "brief_reason_or_null"}
```

---

## Sensitive Content Taxonomy

| Label | Summary | Keywords |
|-------|---------|---------|
| Historical racialized performance | Caricature or performance practices depicting racialized stereotypes such as blackface or yellowface. | blackface, yellowface, minstrel, minstrelsy, caricature, stereotype, brownface, redface, ethnic parody, racial parody, racial impersonation, racial mockery, costume, exoticism, cultural appropriation, racial satire, racist theatre, vaudeville, racial comedy, racial burlesque, mammy, sambo, coon caricature, racial impersonator, racial drag |
| Human remains | Imagery of human remains in archaeological, anthropological, or other contexts. | skeleton, skull, bones, mummy, mummified, corpse, cadaver, grave, burial, coffin, remains, archaeology, anthropology, tomb, ossuary, funerary, embalmed, mortuary, body, exhumed, cranium, fossil, skeletal, ancestral remains, excavation |
| Native American imagery | Depictions of Native/Indigenous persons, regalia, or mascot-related content, including potentially disrespectful uses. | chief, headdress, war bonnet, powwow, ceremonial dress, native regalia, indigenous, tribal costume, totem, tribe, chief illiniwek, native dance, ceremonial feathers, sacred objects, appropriation, tribal identity, indian mascot, indigenous symbols, tribal regalia, spiritual costume, tribal headdress, tribal powwow, native caricature, native impersonation, cultural stereotype |
| Nudity/sexual content | Explicit or suggestive imagery including sexual content, with hard block for minors. | nude, naked, explicit, pornographic, erotic, topless, genitalia, sexual, intercourse, sex, lewd, seductive, suggestive, provocative, stripper, striptease, playboy, centerfold, adult content, orgy, minors, child pornography, pedophilia, molestation, sexual exploitation, rape, assault, incest, porn, obscene |
| Violence/graphic content | Imagery of violence, weapons, injuries, or graphic scenes of harm. | blood, weapon, knife, gun, shooting, stabbing, murder, killing, injury, corpse, beheading, decapitation, gore, explosion, grenade, rifle, pistol, carcass, slaughter, assault, massacre, terrorist, hostage, execution, battle, war, suicide, bomb, violence |
| Hate symbols | Imagery containing hate symbols or iconography associated with hate groups. | swastika, kkk, klan, confederate flag, nazism, neo-nazi, hitler, fascism, white power, 88, heil, skinhead, blood drop cross, 14 words, iron cross, totenkopf, stormfront, racist symbol, white supremacy, third reich, gas chamber, holocaust denial, aryan, fascist salute, racist graffiti |
| Medical/health records | Imagery that may contain identifiable medical records or health data. | medical record, patient chart, hospital, x-ray, mri, ct scan, lab result, diagnosis, treatment, medication, prescription, doctor, nurse, healthcare, surgery, clinic, hospital wristband, health form, insurance card, vaccine, pathology, medical note, confidential, HIPAA, health report |
| Student/PII records | Student-related personally identifiable information or sensitive documents. | student id, social security number, ssn, address, phone number, email, transcript, grades, disciplinary record, enrollment form, financial aid, birthdate, passport, driver license, uin, registration, student loan, FERPA, identity card, contact info, emergency contact, application, admission letter, personal info, resume, cv |
| Other sensitive categories | Additional sensitive contexts not covered above, including terrorism, drugs, and self-harm. | terrorist, isis, al-qaeda, bomb, explosive, extremist, jihad, hostage, narcotics, cocaine, heroin, meth, drug use, drug paraphernalia, overdose, suicide, self-harm, cutting, razor, noose, hanging, poison, anorexia, bulimia, eating disorder, addiction, alcohol abuse, gambling |

---

## Sample Descriptions Generated Before Classification

These descriptions were generated using **Method 1 prompts**, prior to classification.

### Image Example 1 — Human Remains

**NATURAL Description:**
A man is holding a skull with his left hand and examining it closely. The skull has holes in its forehead and chin. The man's right hand is gently touching the skull's nose. Both hands are on the skull's face. The background is black.

**STRICT Description:**
A man is holding up a skull to the face of a dummy head for display purposes.

**Classification result:** ✅ Correctly flagged — `Human remains` (matched keyword: `skull`)

---

### Image Example 2 — Violence/Graphic Content

**NATURAL Description:**
The house, made of wood, stands on a grassy lawn. The roof has partially collapsed under intense heat. The fire is on the right side, with flames billowing outward. Smoke rises into a clear sky. A hose lies on the ground in front of the house.

**STRICT Description:**
A photo of a house with an explosion nearby taken from the outside.

**Classification result:** ✅ Correctly flagged — `Violence/graphic content` (matched keyword: `explosion`)

---

## Method 1: Semantic Similarity-Based Classification

### Overview
This method classifies images based on the semantic similarity of their descriptions to predefined taxonomy keywords. It captures nuanced meaning beyond exact keyword matches.

### Pipeline

**1. Data Loading**
- Load a taxonomy CSV containing labels and associated keywords.
- Load the image descriptions CSV (both short and natural descriptions).

**2. Keyword Parsing**
- Extract keywords from the taxonomy, handling lists, dictionaries, and delimited strings.

**3. Model Embedding**
- Use the SentenceTransformer model (`all-mpnet-base-v2`) to embed taxonomy keywords.
- Normalize and combine short and natural descriptions for embedding.

**4. Semantic Matching**
- Compute cosine similarity between image description embeddings and taxonomy keyword embeddings.
- A match is flagged if similarity ≥ 0.45.
- Output includes: matched labels, matched keywords, boolean sensitive flag.

**5. Results Export**
- Save results to CSV with matched labels, keywords, and detailed JSON of matches.

### Example Outputs

#### Correctly Classified (True Positives)

| Image | Description | Sensitive? | Matched Labels | Matched Keywords |
|-------|-------------|------------|----------------|-----------------|
| `0000230.jpg` | A photo of a house with an explosion nearby taken from the outside. | Yes | Violence/graphic content | explosion |
| `0000207.jpg` | A man is holding up a skull to the face of a dummy head for display purposes. | Yes | Human remains | skull |

#### Misclassified (False Positives)

| Image | Description | Sensitive? | Notes |
|-------|-------------|------------|-------|
| `0000700.jpg` | Two women wearing medieval outfits stand side by side with a man. | Yes | Incorrectly flagged as Native American imagery due to semantic overlap with ceremonial keywords |

### Performance

- **Total processing time (1,000 images):** 9 minutes 6 seconds
- **Description preparation:**
  - Natural prompt (full descriptions): ~4 minutes per batch
  - One-sentence strict prompt: ~1.5 minutes per image
- Embedding is optimized for short text.

### Summary

**Strengths:**
- Captures nuanced meaning beyond exact keyword matches
- Flexible for adding new labels

**Limitations:**
- Computationally heavier than simple keyword matching
- Semantic overlap between unrelated categories can cause false positives

---

## Comparison Table

| Metric | Count | Notes |
|--------|-------|-------|
| Total Labeled Images | 79 / 1000 | Labeled offensive images through Method 1 |
| Manual Review — Correct | 13 / 79 | Clear, confidently correct classifications |
| Wrong Classifications | 8 / 79 | Incorrect labels |
| Subjective / Ambiguous | 58 / 79 | Neither clearly right nor wrong (borderline, interpretation-dependent) |

---

## Results Comparison (Labeled vs. Manually Reviewed)

| Metric | Value |
|--------|-------|
| Accuracy | 16.46% |
| Error Rate | 10.13% |
| Subjective / Ambiguous | 73.4% |

---

## Method 2: LLaVA-Based Image Classification

### Description
This method uses a multimodal LLM (LLaVA) to classify images directly based on their visual content.

**Pipeline:**
1. Collect TIFF images from a folder.
2. Convert images to JPEG format, resizing to a maximum dimension of 4000 pixels.
3. Handle truncated or multi-frame images correctly.
4. Use `llava-llama3` through the Ollama CLI.
5. Parse the JSON response for `offensive`, `category`, and `rationale`.
6. Save results with intermediate saves every 100 images.

### Example Outputs

The model flagged all images as `False` (non-offensive), even when sensitive content was clearly present.

| Filename | Offensive? | Category | Rationale |
|----------|------------|----------|-----------|
| 0000014.tif | False | None | Historical image of a group of people in formal attire posing for a photograph. No apparent offensive content. |
| 0000015.tif | False | None | The image features a historical racialized performance that may be considered offensive. |
| 0000016.tif | False | None | The image is a portrait of a man dressed in formal attire. It does not contain any hateful symbols. |

Note: In row 0000015.tif above, the model correctly identified racialized content in the rationale but still returned `offensive: false` — a clear model limitation.

### Processing Times
- **Average per image:** ~2 to 2.5 minutes
- **Total for 1,000 images (projected):** ~33–40 hours
- No improvement observed from downsampling or batching prompts

### Summary

**Strengths:**
- Capable of understanding visual semantics
- Useful when textual metadata is unavailable

**Limitations:**
- Extremely slow per-image processing
- Failed to detect any offensive or sensitive content in this dataset
- Model may require fine-tuning for historical archival content

---

## Downsampling Evaluation

**Objective:** Assess whether reducing image dimensions by 50% would improve processing efficiency.

**Findings:**
- Descriptive outputs for downsampled images were nearly identical to full-resolution images with no observable loss of semantic detail.
- No measurable processing time improvement. Both original and downsampled images required approximately 2–2.5 minutes per image.
- The primary performance constraint is model inference, not input image size.

**Conclusion:** Downsampling by 50% did not yield performance gains. Maintain original image dimensions unless file size reduction is needed for storage or transfer.

---

## Metadata Extraction and Standardization

### Objective
Extract structured metadata from TIFF image files aligned with **IPTC** and **Dublin Core** standards.

**Purpose of Standardization:**
- **Interoperability:** Metadata can be shared across different systems and platforms.
- **Consistency:** Uniform structure for technical, descriptive, and administrative metadata.
- **Discoverability:** Enhanced search, retrieval, and classification of images.
- **Archival Quality:** Supports long-term preservation and digital asset management compliance.

### Methodology
Using `tifffile`, `Pillow (PIL)`, and `IPTCInfo3`, metadata is extracted under three categories:
- **File-level:** Filename, file size, format type, MIME type.
- **EXIF/TIFF:** Image dimensions, resolution, compression, photometric interpretation.
- **IPTC (where available):** Object name, caption/abstract, keywords.

---

## Summary of Methods, Conclusions, and Recommended Next Steps

### Methods Tested

1. **Semantic Similarity-Based Classification** — Sentence-BERT embeddings, cosine similarity, ~9 min for 1,000 images. Better performance at detecting contextually sensitive content.
2. **LLaVA-Based Image Classification** — Direct multimodal classification, ~2–2.5 min per image. Failed to detect offensive content in this dataset.
3. **Downsampling Test** — No improvement in speed or accuracy. Not recommended unless storage efficiency is needed.
4. **Metadata Extraction** — Successfully extracted EXIF/TIFF/IPTC metadata aligned with archival standards.

### Key Observations

- Out of 1,000 images, only **8–10 were truly sensitive** according to manual review.
- Most images flagged by the semantic method were contextually sensitive but not genuinely offensive — threshold tuning needed.
- Semantic similarity outperformed LLaVA for this dataset.

### Key Conclusions

- Semantic similarity is more effective but requires careful threshold tuning.
- LLaVA, in its current configuration, failed to identify offensive images — fine-tuning recommended.
- Manual review confirms the dataset has very few truly offensive images, making it difficult to validate detection performance without a larger sample.

---

## Next Steps

The next steps depend on Joanne's direction and the desired scope of testing and implementation.

### 1. Expand Testing Sample
- Increase from 1,000 to ~10,000 images for broader coverage and more reliable evaluation.

### 2. Select Processing Approach
- Running both methods in parallel provides the most comprehensive coverage but doubles processing time.
- Either method can be used independently based on project priorities.

### 3. Metadata Expansion
- Confirm which metadata standards to formally align with (IPTC, Dublin Core, or institutional schemas).

### 4. Scaling and Prioritization
- If scaling to large-scale processing, define prioritization criteria:
  - By collection type
  - By historical period or date range
  - By content sensitivity or risk level

### 5. Future Model Enhancement Options

**(a) Integration with Third-Party APIs**
- Google Vision SafeSearch, AWS Rekognition, or Azure Content Moderator for baseline detection.
- Faster results, but higher cost and vendor procurement required.

**(b) Custom Deep Learning Model Development**
- Build a UIUC-specific model trained on institutional image data.
- Use LLaVA to auto-generate initial labels, then manually validate for a training set.
- Enables fine-tuned, domain-specific detection for archival collections.

### 6. Summary Recommendation

| Objective | Recommended Action |
|-----------|-------------------|
| Validation Testing | Expand dataset to 10,000+ images |
| Operational Implementation | Define metadata standards and prioritization strategy |
| Enhanced Automation | Pursue integration with external APIs or custom model fine-tuning |

**Note:** Manual review of 1,000 images found only 8–10 contextually sensitive but not genuinely offensive images, reaffirming the need for expanded testing to better assess true detection performance.
