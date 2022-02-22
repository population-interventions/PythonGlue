BASE_FOLDER='/data/gpfs/projects/punim1497/Repos/PythonGlue/hiic_post/scripts'
cd $BASE_FOLDER
EMAIL=$(cat ~/config/email.txt)
echo $EMAIL

TASK=$(sbatch --mail-user=$EMAIL --mail-type=END hiic_post_jobarray.slurm)
echo $TASK

sleep 3
squeue --me