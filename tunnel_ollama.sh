ssh -N -L 11434:127.0.0.1:11434 halis@10.1.37.223
ssh -t halis@10.1.37.223 "watch -n 1 nvidia-smi" 

