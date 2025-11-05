# Seems trivial DDT, what amazing pAE — The Evolution of Structure Prediction Assessment “Metrics”

Guo Zheng

## Introduction

The AlphaFold series of structural prediction models have ushered in a new era for protein structure prediction and catalyzed significant advancements in AI-based protein design methods. Today, new AI-driven protein design approaches are being published on a weekly basis. As the generation of protein molecules is no longer a bottleneck, the evaluation of design quality has become increasingly critical to the success of these designs. This article will review the evolution of structural assessment metrics—from the era of structure prediction to the current age of protein design—with a particular focus on the computational rationale behind different metrics, aiming to help readers interested in structure prediction and protein design develop a deeper understanding of relevant concepts.

This article is divided into the following five sections:
1. GDT as a Component of LGA
2. From GDT to lDDT
3. The Rise of pLDDT!
4. pTM and pAE: Descended from a Common Lineage as pLDDT
5. The Community-Popularized ipAE and the Playfully Crafted ipSAE Meme


## 1.GDT as a Component of LGA

When it comes to metrics for comparing structural similarity, the Root Mean Square Deviation (RMSD) is the one that most immediately comes to mind.

$$
\text{RMSD} = \sqrt{\frac{1}{N} \sum_{i=1}^{N} \lVert \mathbf{r}_i^{(A)} - \mathbf{r}_i^{(B)} \rVert^2 }
$$
 
$N$: Number of atoms being compared (commonly Cα atoms or all heavy atoms)
$\mathbf{r}_i^{(A)}$: Coordinates of the $i$-th atom in structure A
$\mathbf{r}_i^{(B)}$: Coordinates of the corresponding atom in structure B
$\lVert \cdot \rVert$: Euclidean distance

RMSD directly calculates the Euclidean distance between corresponding atoms in a target structure A and a reference structure B, then averages the result over the number of atoms. Although RMSD is the most conceptually straightforward metric, it has two significant limitations when used for assessing structural similarity. First, RMSD averages the squared differences across all selected atoms, so it is overly sensitive to local deviations. A single large local deviation can disproportionately inflate the overall RMSD value, preventing it from accurately reflecting global structural similarity. This issue is particularly pronounced when aligning the overall structures of multi-domain proteins. Additionally, this averaging effect makes RMSD insensitive to local structural omissions, often leading to an overestimation of similarity for structures with partial missing regions. Second, the calculation of RMSD depends on the alignment between the target and reference structures. Different alignment methods can yield different RMSD values, which complicates the comparison of RMSD results obtained under varying alignment conditions.

To address the limitations of RMSD in structural alignment, the fourth Critical Assessment of protein Structure Prediction (CASP4) introduced the Global Distance Test (GDT) algorithm proposed by Zemla et al. [1]. Unlike RMSD, GDT is a consensus-based method for measuring structural similarity. Specifically, the GDT algorithm proceeds as follows:

1.Identify "alignment centers": For every pair of fragments (with lengths of 3, 5, and 7 residues) from the two structures, a transformation (i.e., translation and rotation) is applied, and the RMSD is calculated. The resulting superimpositions are used to generate an initial list of equivalent residue pairs (using Cα atoms), where each pair consists of one residue from the target structure and one from the reference structure.

2.Exclude "outlier atoms": After obtaining the initial set of atom pairs, identify all pairs where the distance between the atoms in the two structures exceeds a defined threshold. These atoms are excluded from subsequent steps.

3.Iterative alignment and exclusion: The remaining structures are realigned, and the outlier exclusion step is repeated. This cycle continues until the set of atoms used in two consecutive iterations remains unchanged.

The following provides a detailed explanation:

First, identifying alignment centers. Like RMSD, GDT relies on structural alignment to assess similarity. Thus, the first step involves systematically testing all possible alignments to find the one that maximizes the initial number of equivalent residues. This is achieved by selecting relatively small fragments from both structures (the fragments must be large enough to produce stable superimpositions—too small and the results become unreliable for identifying equivalent residues; too large and they restrict the search space for optimal alignment). Each fragment pair is aligned, and the number of equivalent residues under that alignment is counted.

Next, excluding outlier atoms. For the initial list of equivalent residues, the Euclidean distance *d* between each pair of equivalent atoms (one from the target structure, one from the reference) is calculated. If this distance exceeds a predefined cutoff (e.g., 2Å, 4Å, 8Å), the atom pair is considered an outlier and is removed from both the target and reference structures. The list is then updated accordingly.

Finally, the iterative alignment and exclusion process. The iteration ensures that the alignment is not skewed by the influence of large outliers. By removing outliers and realigning, the algorithm more accurately assesses whether the remaining atoms in the target structure all fall within the required distance threshold. If not, the cycle continues. Once two consecutive iterations yield identical atom sets, the GDT score between the two structures is calculated.

For a given distance threshold *d*, the GDT score is calculated as:

$$
GDT(d_{cutoff}) = \frac{N_{aligned}(d_{cutoff})}{N_{total}} \times 100\%
$$

$N_{aligned}(d_{cutoff})$: Number of aligned atom pairs satisfying the distance cutoff criterion.
$N_{total}$: Total number of residues.

As can be seen from the formula, GDT measures the percentage of residues that can be successfully aligned under a given distance cutoff. Two commonly used GDT metrics are GDT-TS and GDT-HA:

GDT_TS (Total Score) is the average of the results at four distance cutoffs: 1, 2, 4, and 8 Å:
$$
GDT\_TS = \frac{ GDT(1) + GDT(2) + GDT(4) + GDT(8) }{4}
$$
GDT_HA (High Accuracy) is the average of the results at four more stringent distance cutoffs: 0.5, 1, 2, and 4 Å (Formula same as above).

Furthermore, a review of the aforementioned steps reveals that the procedure remains applicable even when the target and reference structures are of unequal sequence length. Consequently, unlike RMSD, GDT-based comparison does not depend on sequence length equivalence.

It is important to note that (in contrast to the lDDT metric discussed later), both RMSD and GDT provide global structural scores and do not yield residue-level evaluations. (In fact, in Zemla's original publication, GDT was introduced as a component of the Local-Global Alignment (LGA) method. However, the other component—the Longest Continuous Segment (LCS) algorithm—is relatively straightforward and will not be elaborated here.)

## 2. From GDT to lDDT

As previously mentioned, the GDT score represents the average proportion of superimposable atoms across a set of predefined thresholds. A key advantage of GDT is that significantly deviated atoms do not substantially impact the score, while missing fragments in predictions lead to score reduction. However, such global superposition scores still face a major limitation: when aligning multi-domain proteins with flexible inter-domain arrangements, the global superposition tends to be dominated by the largest (most similar) domain, preventing proper alignment of smaller domains and compromising scoring accuracy.

Consequently, the local Distance Difference Test (lDDT) was introduced in CASP9 to evaluate how well local atomic interactions from the reference structure are reproduced in predictions [2]. 

The lDDT calculation proceeds as follows:

1.For a specific atom A in the reference structure, identify all non-covalent atoms within an inclusion radius R₀ (a predefined threshold). The pairwise distances between these atoms and atom A define the local distance set L for atom A.

2.For the corresponding atom A' in the predicted structure, compare its local distance set L' with reference set L. A distance is retained if it matches the reference within a given thresholds; excluded if either defining atom is missing or the distance deviation exceeds thresholds.

3.Calculate the proportion of retained distances at specified thresholds. 

For partially symmetric residues (e.g., glutamate, aspartate, valine, tyrosine, leucine, phenylalanine), both possible atom naming schemes are evaluated, with the higher lDDT value retained.

The final lDDT score averages proportions across four thresholds (0.5Å, 1Å, 2Å, 4Å—identical to GDT-HA thresholds). 

While this description implies a static local distance set definition, we must recognize that even evaluating a single residue requires aggregating distance sets for all its atoms. By calculating the proportion of the local distance set from this residue in the reference structure that is preserved in the corresponding residue's local distance set in the target structure, we can quantitatively assess how well the local atomic interactions of this residue are reproduced in the predicted structure. Calculating the proportion of preserved local distances for each residue yields the per-residue lDDT, which when averaged produces the global lDDT score.
The lDDT algorithm naturally extends to multi-conformation structural comparisons by recording each residue's local environments across conformations and verifying their preservation in target structures. 

Metaphorically, if GDT resembles sculpting—progressively carving away poorly aligned atoms to reveal consensus regions—lDDT operates like a fixed-radius microscope that catalogs each residue's "neighbors" in the reference structure, then checks their preservation in predictions. This approach particularly benefits residues at domain interfaces or edges: with appropriate R₀ selection, their neighbors remain consistently defined, avoiding artificial discrepancies between reference and predicted structures.

The inclusion radius R₀ in lDDT was optimized against GDC-all scores (the all-atom GDT variant with thresholds from 0.5Å to 10Å at 0.5Å increments). Developers tested R₀ values from 2Å to 40Å, finding optimal agreement with GDC-all at 15Å while eliminating manual domain segmentation. Thus, 15Å became the default inclusion radius. This established an alignment-free consistency metric resilient to domain motions. (However, while lDDT excels as a prediction assessment metric, its utility in structural clustering remains limited.)

 
Figure 1. Concordance between the inclusion radius and GDC-all scores [2].

## 3. The Rise of pLDDT!



 
“The Rise of pLDDT!”, image generated by Vidu and nano-banana


Many people likely first encountered the "lDDT" metric through AlphaFold 2 (AF2). Although this metric has the extensive background detailed in the previous paragraph, I chose DDT as the title to give readers a general expectation of the content. 

Returning to pLDDT, it is the predicted per-residue lDDT-Cα (lDDT calculated for Cα atoms) output alongside the atomic coordinates of the predicted structure by the end-to-end structure prediction model AF2. Its purpose is to provide a confidence estimate for the output structural model, hence the AF2 authors termed this metric pLDDT (predicted lDDT) [3].

Unlike the structure comparison metrics discussed above, which require a reference structure for calculation, pLDDT is output simultaneously with the model's predicted structure and does not depend on the existence of a reference structure. Understanding this requires clarifying two points: how pLDDT is trained, and how it is output.

First, let's discuss the training of pLDDT. During AF2's training, alongside the main task of predicting residue 3D coordinates, several auxiliary tasks are included, among them the prediction of structural confidence metrics like pLDDT. The overall training strategy uses high-resolution structural data (X-ray structures at 0.1–3.0 Å) as references. The per-residue lDDT-Cα is computed between the model's predicted structure and the reference structure. The model is then trained to make its predicted pLDDT gradually approximate this calculated lDDT-Cα value.

In implementation, after calculating the lDDT-Cα, this score is discretized into 50 bins, producing a 50-dimensional one-hot vector. (Simply put, if the calculated lDDT-Cα score is 81, for subsequent processing, based on 81 falling into the [80, 82) bin – one of 50 pre-defined bins of width 2 spanning [0, 100] – the model sets the value corresponding to the [80, 82) bin dimension to 1 and all other dimension values to 0, resulting in a "one-hot " and 49 cold vector). The model then calculates the cross-entropy loss between the output pLDDT and this one-hot vector. 

Here, we will briefly introduce information entropy and cross-entropy.

For a discrete random variable $X$ following distribution $p(x)$, the information entropy is defined as:
$$
H(p) = - \sum_x p(x) \log p(x)
$$

Here, information entropy describes the average information content of distribution $p$, calculated by summing the logarithm of each possible value's probability weighted by its probability. The negative sign ensures the entropy is positive.

If the distribution is deterministic—for instance, if $X$ is a constant (p=1)—the entropy is 0.
If X can take two values, each with probability 0.5, the entropy is $0.5 \times 1 + 0.5 \times 1 = 1$.
If X can take four values, each with probability 0.25, the entropy is $0.25 \times 2 \times 4 = 2$.
As shown, the more values a variable can take, the higher the information entropy, indicating greater average information content.

Given two distributions—the true distribution $p(x)$ and the predicted distribution $q(x)$—the cross-entropy is defined as:

$$
H(p, q) = - \sum_x p(x) \log q(x)
$$

Meaning: If the true distribution is $p$, but we use the predicted distribution $q$ to encode it, $H(p, q)$ represents the average information content required.
When $q = p$, cross-entropy is minimized, and $H(p, q) = H(p)$.
When $q$ deviates from $p$, cross-entropy increases.

For example, consider a multiple-choice question where the correct answer is C:
If the model’s predicted probability distribution is A=0.1, B=0.2, C=0.7, D=0.0, the cross-entropy loss is $-\log(0.7)$, which is relatively small, indicating a good prediction.
If the model’s predicted distribution is A=0.9, B=0.1, C=0.0, D=0.0, the cross-entropy loss becomes $-\log(0.0)$, approaching infinity, meaning the model’s prediction is completely off.
The researchers behind AlphaFold2 train the model’s predicted pLDDT distribution using a cross-entropy loss between the predicted pLDDT distribution and the lDDT-C calculated from the predicted and true structures. Since the lDDT-C per residue is discretized into a one-hot “1 hot + 49 cold” vector, the loss only needs to take the negative log-likelihood of the predicted probability corresponding to the correct bin:

$$
L = H(p, q) = -\log q(k)
$$

where k is the bin to which the true lDDT-C belongs.

Because the predicted pLDDT is not one-hot (it assigns non-zero probability to all 50 bins), if the model assigns high probability to the correct bin (close to 1), the loss is small; if the probability is low (close to 0), the loss diverges. By optimizing this loss over high-quality structural data, the model learns to make accurate confidence estimates during inference.

Once the training process for pLDDT is understood, we can look at how it is produced in practice.

To simplify, the description above did not distinguish between steps, but in fact the pLDDT prediction involves two main components. First, the AlphaFold2 structure module outputs several internal representations. Then, the pLDDT prediction module (referred to here as the pLDDT head) reads the relevant representations and outputs the pLDDT distribution. During training, the cross-entropy between pLDDT and lDDT-C is backpropagated through the model. After training, during inference, the pLDDT head follows the same path and directly outputs pLDDT for user reference.

Specifically, the structure module outputs three kinds of representations:
MSA representation
Pair representation
Single representation (the row corresponding to the original input sequence extracted from the MSA representation)

The pLDDT head takes the final single representation as input, passes it through two linear layers with ReLU activations, followed by one more linear layer and a softmax, producing a 50-dimensional probability distribution. This 50-dimensional vector is the per-residue pLDDT distribution. Taking the expectation of this distribution yields a pLDDT score for each residue. Averaging across all residues yields the overall structural pLDDT.

The transition from lDDT to pLDDT represents a shift from reference-dependent to reference-free structure quality assessment. 

Although the reasoning above explains this technically, I still want to give an intuitive interpretation: Why is the model able to estimate its own confidence?

Because during inference, the model generates internal representations that differ depending on how well the structure can be predicted. As part of training, the pLDDT head learns to recognize which internal representations correspond to well-predicted structures and which correspond to uncertain ones. Therefore, after training, when given a new input, the model can internally “sense” how confident it should be in its prediction and reflect that in the pLDDT output. It is similar to a student who not only scores well on exams, but also takes enough practice tests to develop a sense of self-assessment. While answering questions, the student still has the mental capacity to reflect on how well each part was answered. As a result, when leaving the exam room—before the official scores are released—the student can already estimate their score with considerable accuracy. (Up to this point, we have explained why AlphaFold2 and subsequent models are able to directly output an assessment of their prediction quality.)

## 4. pTM and pAE: Descended from a Common Lineage as pLDDT

In the AF2 paper, pLDDT was introduced together with pAE and pTM. To explain pAE, we first need to define aligned error (AE). In the original paper, aligned error is defined as follows: for a given residue i, the model aligns the backbone atoms N, Cα, and C of residue i in the predicted structure to the corresponding atoms in the experimental structure. After this alignment, the AE for residue pair (i, j) is the distance between the Cα atom of residue j in the predicted structure and the Cα atom of residue j in the experimental structure. Thus, pAE is the model’s prediction of this aligned error.

Similar to pLDDT, pAE is also trained using a cross-entropy loss function. The key difference is that the pAE prediction head takes the pair representation as input. The actual aligned errors are discretized into 64 bins. The model is then trained by computing the cross-entropy between the predicted pAE distribution and the true aligned error bin, enabling the pAE prediction head to learn to estimate the aligned error for each residue pair. During inference, the pAE head reads the same pair representation and outputs the probability distribution over the aligned error bins for each residue pair. Taking the expectation of this distribution yields the pAE value for that residue pair: 

$$
PAE_{ij} = \sum_{b=1}^{64} p_{ij}^b \, \Delta_b
$$

* $\Delta_b = (b - 0.5)\times 0.5$，which represents the center value of the b-th bin (0.25 Å, 0.75 Å, …, 31.75 Å)；
* $p_{ij}^b$ denotes the probability that the residue pair $(i, j)$ falls into the b-th bin；
* $\sum_{b=1}^{64} p_{ij}^b = 1$。

Although the AF2 paper does not present pAE as a named metric, the AF2 database displays pAE alongside pLDDT as an important confidence measure for users. 

In addition to pLDDT, which reflects local prediction confidence, and pAE, which reflects pairwise alignment error, the AF2 paper also introduces pTM, which assesses the confidence of the overall structural alignment. pTM is based on the TM-score, a commonly used metric for evaluating global structural topology similarity between proteins.

$$
TM = \max_{\text{alignments}} \left[ \frac{1}{L_{\text{target}}} \sum_{j \in \text{common residues}} \frac{1}{1 + \left(\frac{d_j}{d_0}\right)^2} \right]
$$

Here, $d_j$ denotes the distance between the C$\alpha$ atom of residue $j$ in the predicted structure and the C$\alpha$ atom of the corresponding residue $j$ in the experimental structure under a given alignment. $d_0$ is a scaling factor used to reduce or eliminate the dependence of the TM-score on protein length when comparing unrelated proteins.

pTM is obtained by substituting the model-predicted aligned error (PAE_{ij}) into the original TM-score formula, thereby deriving the pTM calculation expression: 

$$
pTM = \max_{i} \left[ \frac{1}{L} \sum_{j=1}^{L} \frac{1}{1 + \left(\frac{PAE_{ij}}{d_0}\right)^2} \right]
$$

For residue i, $pTM_i$ is computed by averaging the pAE values between residue i and all other residues along the chain. The maximum $pTM_i$ over all residues in the chain is then taken as the pTM of the entire protein. Since the training procedure and discretization of scores for pTM and pAE are essentially the same, we will not repeat the explanation here.

At this point, the two major metrics in the question have been introduced. It is worth noting that before I began studying these metrics in depth, I once guessed how pLDDT and pAE might be computed. At the time, I assumed that pLDDT was obtained by comparing multiple independent predictions of the same sequence, thereby estimating structural confidence without using any reference structure. I similarly thought pAE was computed by aligning multiple predicted structures to estimate the magnitude of pairwise alignment error. At the time, this seemed quite reasonable—but it turns out to be entirely incorrect.

In reality, both pLDDT and pAE are learned from comparisons with real structures during training, and the model learns to directly infer confidence during inference based on its own internal representations. This also implies that AF2’s confidence estimates are influenced by the structural patterns present in the training set.

As a result, two types of misestimation may occur: 
1. Underestimation: The predicted structure is actually accurate, but differs from the distribution of similar structures in the training set, causing pLDDT to be lower than appropriate.
2. Overestimation: The predicted structure is not very accurate, but happens to resemble familiar patterns in the training set, causing pLDDT to be artificially high.

Likewise, pAE can also be either overestimated or underestimated for similar reasons. This suggests that pAE may have inherent limitations, which we will revisit later when discussing ipAE.

(An open question for the reader: Why is pAE asymmetric between residue pairs?)

## 5. The Community-Popularized ipAE and the Playfully Crafted ipSAE Meme
 
“pAE will tell you the answer”, image generated by Vidu and nano-banana



Based on the discussion above, the following interface-related PPI confidence metrics should now appear quite natural. After releasing AlphaFold2, the DeepMind team introduced AlphaFold-Multimer, a model specifically designed for complex structure prediction【4】. In the AlphaFold-Multimer preprint, the authors defined an interface version of pTM, namely ipTM (interface predicted TM). Unlike pTM, which evaluates the TM-score based on aligned errors within a single chain, ipTM specifically measures the TM-score using aligned errors between residues across different chains. 

Thus, the formula for computing ipTM is identical to that of pTM, with the only requirement being that residues i and j must come from different chains. The authors further compared ipTM to DockQ, a widely used score for assessing complex quality in protein docking, and reported strong consistency between the two.

However, after ipTM was proposed, several research groups noted that the ipTM score is sensitive to sequence length. That is, even with the same interface structure, variations in input sequence length can lead to different ipTM scores, and non-interacting segments may yield ipTM values comparable to those of true interfaces【5】. This indicates that ipTM may not be a reliable scoring metric for interaction screening. Meanwhile, other researchers proposed pDockQ, which follows a similar rationale as ipTM for interaction prediction【6】.

The studies above primarily focus on predicting structures of known complexes or natural protein–protein interactions. For de novo designed binders, the most effective interaction scoring metric was first clearly articulated in a 2023 Nature Communications publication【7】. This metric is pAE_interaction.

The computation of pAE_interaction is straightforward: take the PAE matrix predicted by AlphaFold2, extract the inter-chain region, and compute the average. Because the PAE matrix contains two inter-chain blocks, one representing binder residues (rows) vs. target residues (columns), and the other representing target residues (rows) vs. binder residues (columns), both averages are computed and then averaged again to obtain pAE_interaction. The authors demonstrated through experiments and retrospective dataset analysis that this score provides strong predictive performance for interaction accuracy. 

Indeed, even before this paper, researchers had already begun to recognize the advantage of ipAE-based metrics over ipTM for interaction assessment, leading to further refinements such as actifpTM【9】 and ipSAE【10】.

In a recent preprint, researchers benchmarked these related metrics to determine which performs best. They concluded that ipSAE exhibits the strongest predictive ability【11】. Therefore, we conclude with an introduction to ipSAE.

ipSAE stands for Interaction Prediction Score from Aligned Errors. The name also plays on the Latin phrase Rēs ipsae loquuntur (“the thing speaks for itself”), implying that AlphaFold’s own output is sufficient to justify the prediction confidence.

As noted earlier, the original ipTM calculation considers PAE over the entire chain, making ipTM sensitive to chain length and non-interacting disordered regions. To address this, the authors of ipSAE propose selecting only inter-chain residue pairs with sufficiently low aligned error and computing a TM-like score using only these pairs. 

Thus, the ipSAE scoring formula is given by: 

$$
ipSAE(A \to B) = \max_{i \in A} \Bigg[ \mathrm{mean}_{j \in B, PAE_{ij}<cutoff} \Big(\frac{1}{1+(PAE_{ij}/d0)^2}\Big) \Bigg]
$$

Additionally, the d₀ parameter in the TM formula is adaptively scaled based on the number of high-confidence inter-chain residue pairs: 

$$
d0 =
\begin{cases} 
1.24\sqrt{L_{PAE<cutoff}-15} - 1.8, & L \ge 27 \\
1, & L < 27
\end{cases}
$$

For a given pair of chains, the final ipSAE score is taken as the maximum of the two asymmetric forms:

$$
ipSAE(A,B) = \max[ipSAE(A \to B), ipSAE(B \to A)]
$$
Although the formulas above appear somewhat complex, the core idea is straightforward: ipSAE selects only inter-chain residue pairs with sufficiently reliable PAE (less than a given threshold, typically 10 Å), and applies a TM-score-like normalization to them. At the same time, the d_0parameter is dynamically adjusted based on the number of high-confidence residue pairs, preventing a small number of low-PAE pairs from disproportionately inflating the score, which is a known issue in ipTM.

Due to the inherent asymmetry of PAE between chains, the authors take the maximum of the two directional scores as the final inter-chain ipSAE value. Since smaller PAE indicates higher prediction confidence, the TM-like normalization ensures that a larger ipSAE corresponds to a more reliable predicted interaction. By choosing the larger directional score, the authors effectively assume that confidence in the interaction is justified as long as one chain’s perspective aligns strongly with the predicted contact pattern.

However, subsequent benchmarking studies have suggested that ipSAE_min (taking the minimum of the two directional scores instead of the maximum) can sometimes perform slightly better than ipSAE_max. This difference may depend on dataset characteristics and evaluation criteria.

In summary, ipSAE represents a useful and practical metric for assessing protein–protein interaction confidence, particularly in contexts involving binder design and interface prediction.

Afterword

There are many scoring metrics related to structure prediction, and new ones continue to be proposed. This article is a summary I compiled while trying to understand pLDDT and ipSAE by tracing the literature backward, so some metrics that are not directly along this developmental path (such as DockQ, which was mentioned briefly) were not discussed in detail. I hope this article will be useful for readers interested in scoring methods for protein structure prediction and protein design.

【1】Zemla, Adam. "LGA: a method for finding 3D similarities in protein structures." Nucleic acids research 31.13 (2003): 3370-3374.  
【2】Mariani, Valerio, et al. "lDDT: a local superposition-free score for comparing protein structures and models using distance difference tests." Bioinformatics 29.21 (2013): 2722-2728.  
【3】Jumper, John, et al. "Highly accurate protein structure prediction with AlphaFold." nature 596.7873 (2021): 583-589.  
【4】Evans, R., et al. "AlphaFold-Multimer Protein complex prediction with." BioRxiv (2022).  
【5】Bret, Hélène, et al. "From interaction networks to interfaces, scanning intrinsically disordered regions using AlphaFold2." Nature communications 15.1 (2024): 597.  
【6】Bryant, Patrick, Gabriele Pozzati, and Arne Elofsson. "Improved prediction of protein-protein interactions using AlphaFold2." Nature communications 13.1 (2022): 1265.  
【7】Bennett, Nathaniel R., et al. "Improving de novo protein binder design with deep learning." Nature Communications 14.1 (2023): 2625.  
【8】Refer to “github.com/nrbennet/dl_binder_design/blob/cafa3853ac94dceb1b908c8d9e6954d71749871a/af2_initial_guess/predict.py” lines 188–211  
【9】Varga, Julia K., Sergey Ovchinnikov, and Ora Schueler-Furman. "actifpTM: a refined confidence metric of AlphaFold2 predictions involving flexible regions." Bioinformatics 41.3 (2025): btaf107.  
【10】Dunbrack Jr, Roland L. "Rēs ipSAE loquunt: What's wrong with AlphaFold's ipTM score and how to fix it." bioRxiv (2025).  
【11】Overath, Max Daniel, et al. "Predicting Experimental Success in De Novo Binder Design: A Meta-Analysis of 3,766 Experimentally Characterised Binders." bioRxiv (2025): 2025-08.  








