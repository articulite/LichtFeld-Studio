@echo off
cd /d "C:\gitprojects\LichtFeld-Studio"
echo Starting LichtFeld Studio Training with 9-View Angled-Ceiling Dataset...
.\build-windows-release\LichtFeld-Studio.exe -d "C:\gitprojects\working-dir-spheresfm\colmap\sparse-cubic-angled" -o "C:\Users\Admin\Pictures\Lichtfield\indoor-test-1\output_kgs_angled" --strategy kgs --enable-mip --progressive-resolution --use-depth-loss --depth-loss-weight 0.05 --use-normal-loss --normal-loss-weight 0.005 --normal-consistency-weight 0.005 --depth-bilateral --depth-bilateral-radius 1 --mask-mode ignore --max-cap 2000000 --eval --train
pause
