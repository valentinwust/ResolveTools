import numpy as np
import pandas as pd
import anndata

##############################
### Assign counts with Segmentation
##############################

def assign_counts_from_segmentation(countsfile, metafile, segmentationfile, segmentationkey, outputfile, roikey):
    """ Assign counts, using a full cell segmentation.
    """
    rim = ResolveImage(countsfile)
    rim.add_metadata(metafile)
    segmentation = np.load(segmentationfile)[segmentationkey]
    
    def find_cell(mask, target):
        return mask[target[0],target[1],target[2]]
    rim.full_data["cell"] = [find_cell(segmentation, target) for target in np.asarray(rim.full_data[["z","y","x"]])]
    print("Started with",len(rim.full_data),"counts, could not assign",(rim.full_data["cell"]==0).sum(),"of those.")
    rim.full_data["cell"] = rim.full_data["cell"].astype(int)
    
    var = rim.genes.copy()
    obs = pd.DataFrame(np.unique(rim.full_data["cell"])[1:,None], columns=["MaskIndex"])
    obs["CellName"] = roikey+"_"+obs["MaskIndex"].astype(str)
    obs.index = np.asarray(obs["MaskIndex"])
    obs["ROI"] = roikey
    
    counts = pd.DataFrame(np.zeros((obs.shape[0],var.shape[0])),
                          columns = np.asarray(var["GeneR"]),
                          index = obs.index)
    def count_gene(gene, rim, counts, distancecutoff=50):
        cell = rim.full_data.loc[rim.full_data["GeneR"]==gene,"cell"]
        u, c = np.unique(cell[cell!=0], return_counts=True)
        counts.loc[u,gene] = c
    for gene in var["GeneR"]:
        count_gene(gene, rim, counts)
    
    obs.index = np.asarray(obs["CellName"])
    counts.index = np.asarray(obs["CellName"])
    
    adata = anndata.AnnData(counts, dtype=np.float32, obs = obs, var = var )
    
    adata.obs["MouseGeneCount"] = counts[adata.var.loc[adata.var["Species"]=="Mouse","GeneR"]].sum(axis=1)
    adata.obs["HumanGeneCount"] = counts[adata.var.loc[adata.var["Species"]=="Human","GeneR"]].sum(axis=1)
    adata.obs["MouseGeneShare"] = counts[adata.var.loc[adata.var["Species"]=="Mouse","GeneR"]].sum(axis=1)/counts.sum(axis=1)
    adata.obs["HumanGeneShare"] = counts[adata.var.loc[adata.var["Species"]=="Human","GeneR"]].sum(axis=1)/counts.sum(axis=1)
    
    adata.write_loom(outputfile)