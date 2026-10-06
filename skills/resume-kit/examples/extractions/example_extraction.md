# Deep Learning-Guided Screening of Thermostable Enzyme Variants for Industrial Biocatalysis

## Metadata

- **Authors:** J. Chen, R. Nakamura, S. Patel, K. Holmberg, M. Rivera
- **Year:** 2025
- **Journal:** ACS Catalysis
- **DOI:** 10.1021/acscatal.2025.XXXXX
- **Author position:** First author
- **Status:** Published (online Jan 2025)
- **Citations:** 12 (as of Mar 2026)

## Methods & Tools

- **Protein structure:** AlphaFold2 for initial structure prediction, Rosetta for refinement
- **ML framework:** Fine-tuned protein language model (ESM-2, 650M parameters)
  - Architecture: transformer encoder with task-specific regression head
  - Training data: ~45,000 experimentally measured melting temperatures from ProTherm/FireProtDB
  - Training/validation/test split: 70/15/15
- **MD engine:** GROMACS 2023 with CHARMM36m force field
- **Enhanced sampling:** Replica exchange MD (T-REMD) for conformational landscape mapping
- **Docking:** AutoDock Vina for substrate binding pose prediction
- **Analysis:** Python (BioPython, MDAnalysis, ProDy), PyMOL for visualization
- **Plotting:** matplotlib, seaborn for fitness landscapes and stability distributions
- **Hardware:** 320 GPU-hours on university HPC (NVIDIA A100)
- **Workflow:** Snakemake pipeline for automated screen-simulate-validate cycles
- **Version control:** Git, DVC for dataset versioning

## Key Results (with numbers)

- Fine-tuned ESM-2 model achieving Spearman correlation of 0.82 on melting temperature prediction across 12 enzyme families
- Validation on held-out test set: MAE = 2.3 degrees C, R-squared = 0.79
- Screened 8,500 single- and double-mutant variants in silico in 48 hours (vs. estimated 14 months experimentally)
- Identified 7 thermostable variants of lipase B with predicted melting temperature 15+ degrees C above wild type
- Experimental collaborators confirmed stability improvement for 5 of 7 candidates (differential scanning calorimetry)
- 200-ns replica exchange MD simulations revealed stabilizing salt bridge networks absent in wild type
- Discovered sequence-dependent unfolding pathway divergence above 340 K across the variant library
- Achieved 3,000x throughput improvement over experimental screening for equivalent hit rate
- Transfer learning from ESM-2 reduced required training data by 60% compared to training from scratch
- Total compute: 320 GPU-hours (training) + 1,200 CPU-hours (MD validation) vs. estimated 18 months wet-lab

## Collaboration & Scope

- **PI / Senior author:** K. Holmberg (Lakewood University, computational biology group lead)
- **J. Chen's role:** Designed ML pipeline, fine-tuned protein language model, ran all MD simulations, wrote manuscript draft
- **R. Nakamura:** Curated training data from ProTherm/FireProtDB databases
- **S. Patel:** Experimental validation of top-7 candidates (DSC and activity assays)
- **M. Rivera:** Snakemake workflow design (co-developed with J. Chen)
- **Scope:** Single-lab project with experimental validation collaboration

## Provenance

- **Publication status:** Published, peer-reviewed
- **Peer review notes:** 3 reviewers, 1 revision cycle, accepted after minor revisions
- **Claiming rules:**
  - FULL ownership: ML pipeline design, model fine-tuning, MD simulations, manuscript writing
  - SHARED ownership: Snakemake workflow (co-developed with M. Rivera)
  - NO ownership: Training data curation (R. Nakamura), experimental validation (S. Patel)
- **Safe verbs for bullets:** Developed, Designed, Built, Fine-tuned (for ML work); Co-developed (for workflow)
- **Unsafe claims:** Cannot claim experimental validation; cannot claim sole credit for workflow automation
- **Data availability:** Trained model weights deposited on Hugging Face (open access)
- **Code availability:** Screening pipeline on GitHub (public repo, MIT license)

## Resume Bullet Seeds

1. **[STAR: Protein language model for stability prediction]**
   Situation: Enzyme thermostability screening bottlenecked by experimental throughput.
   Task: Build ML model for rapid stability prediction across enzyme families.
   Action: Fine-tuned ESM-2 protein language model on 45K experimental melting temperatures.
   Result: 0.82 Spearman correlation, screened 8,500 variants in 48 hrs, 5/7 top hits confirmed.

2. **[STAR: Thermostable enzyme discovery]**
   Situation: Industrial biocatalysis requires enzymes stable above 70 degrees C.
   Task: Identify lipase B variants with substantially improved thermostability.
   Action: Combined ML-accelerated screening with 200-ns replica exchange MD validation.
   Result: Identified 7 variants with 15+ degrees C stability gain, 5 experimentally confirmed.

3. **[STAR: Transfer learning pipeline]**
   Situation: Limited labeled data for enzyme stability prediction.
   Task: Reduce training data requirements while maintaining accuracy.
   Action: Co-developed transfer learning pipeline from ESM-2 pretrained representations.
   Result: 60% reduction in required training data while maintaining sub-3 degrees C MAE.

4. **[STAR: Conformational dynamics]**
   Situation: Static structure predictions cannot capture unfolding pathways.
   Task: Reveal stabilizing interactions in engineered enzyme variants.
   Action: Ran 200-ns T-REMD simulations of wild-type and 7 top variants at 300--400 K.
   Result: Discovered stabilizing salt bridge networks and sequence-dependent unfolding divergence at 340 K.
