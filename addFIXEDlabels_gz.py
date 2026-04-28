#!/usr/bin/env python

import numpy as np
import os
import argparse


def parse_fixed_positions(fixed_str):
    """
    Parse strings like:
        1,2,5,10
        1-5,8,10-12
    into a sorted zero-based index list.
    """
    positions = set()

    if not fixed_str:
        return []

    for part in fixed_str.split(","):
        part = part.strip()
        if not part:
            continue

        if "-" in part:
            start, end = part.split("-", 1)
            start = int(start)
            end = int(end)
            if start > end:
                raise ValueError(f"Invalid range in --fixed: {part}")
            for pos in range(start, end + 1):
                positions.add(pos - 1)  # convert to 0-based
        else:
            positions.add(int(part) - 1)  # convert to 0-based

    return sorted(positions)


# Parse Arguments
parser = argparse.ArgumentParser()
parser.add_argument("--pdbdir", type=str, required=True)
parser.add_argument("--trbdir", type=str, required=False, default=None)
parser.add_argument("--fixed", type=str, default=None,
                    help="Manually specify fixed residues, e.g. '1,2,5' or '1-5,8,10-12'. "
                         "These are 1-based residue numbers as written into the PDB remark.")
parser.add_argument("--verbose", action="store_true", default=False)
args = parser.parse_args()

pdb_list = os.listdir(args.pdbdir)

# Parse manual fixed positions once
manual_indices = None
if args.fixed is not None:
    try:
        manual_indices = parse_fixed_positions(args.fixed)
    except Exception as e:
        raise ValueError(f"Failed to parse --fixed: {e}")

for pdb in pdb_list:

    if not pdb.endswith(".pdb"):
        if args.verbose:
            print(f"Skipping {pdb} as it is not a PDB file")
        continue

    pdb_path = os.path.join(args.pdbdir, pdb)

    # Priority 1: manually specified fixed residues
    if manual_indices is not None:
        indices = manual_indices
        if args.verbose:
            print(f"Using manually specified FIXED residues for {pdb}: "
                  f"{[i + 1 for i in indices]}")

    # Priority 2: original TRB-based logic
    else:
        if args.trbdir is None:
            print(f"Error: No --fixed provided and no --trbdir available for PDB {pdb}")
            continue

        trb_path = os.path.join(args.trbdir, f'{pdb.split(".")[0]}.trb')

        if not os.path.exists(trb_path):
            print(f"Error: TRB file not found for PDB {pdb}")
            continue

        data = np.load(trb_path, allow_pickle=True)

        if 'receptor_con_hal_pdb_idx' in data:
            # Identify the last residue number in A chain
            last_res_id = int(data['receptor_con_hal_pdb_idx'][0][1]) - 1

            # Identify where inpaint_seq is True, i.e. kept fixed
            indices = np.where(data['inpaint_seq'][:last_res_id])[0]
        else:
            # Identify where inpaint_seq is True in the only chain
            indices = np.where(data['inpaint_seq'])[0]

        if args.verbose:
            print(f"Adding FIXED labels to {pdb} from TRB at positions {indices}")

    remarks = []
    for position in indices:
        remark = f"REMARK PDBinfo-LABEL:{position+1: >5} FIXED"
        remarks.append(remark)

    remarks_str = '\n'.join(remarks)
    with open(pdb_path, 'a') as f:
        f.write('\n')
        f.write(remarks_str)