#!/bin/bash
#SBATCH --nodes=1
#SBATCH --partition physical
#SBATCH -A punim1497
#SBATCH --time 0:01:00 
#SBATCH --cpus-per-task=1
#SBATCH --job-name="HIIC-post-process"
#SBATCH --array=0-1399

module load python/3.8.6
module load web_proxy

BASE_FOLDER='/data/gpfs/projects/punim1497/Repos/PythonGlue/hiic_post'
cd $BASE_FOLDER

date '+%A %W %Y %X'

pip install --user pandas
pip install --user tqdm
pip install --user numpy

python process_run.py ${SLURM_ARRAY_TASK_ID}

date '+%A %W %Y %X'