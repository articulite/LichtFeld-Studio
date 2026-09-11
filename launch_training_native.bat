@echo off
cd /d "C:\gitprojects\LichtFeld-Studio"
echo Starting LichtFeld Studio Training with Depth Supervision and Native GUI...
.\build-windows-release\LichtFeld-Studio.exe -d "C:\gitprojects\working-dir-spheresfm\colmap\sparse-cubic" -o "C:\Users\Admin\Pictures\Lichtfield\indoor-test-1\output_kgs_depth" --strategy kgs --enable-mip --progressive-resolution --use-depth-loss --use-normal-loss --normal-consistency-weight 0.005 --depth-bilateral --depth-bilateral-radius 1 --mask-mode ignore --max-cap 2000000 --eval --train
pause
