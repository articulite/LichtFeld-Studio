@echo off
cd /d "C:\gitprojects\LichtFeld-Studio"
echo Starting LichtFeld Studio Training for 100k steps (9-View Angled, Anchored Ceiling, Pure Photometric)...
.\build-windows-release\LichtFeld-Studio.exe -d "C:\gitprojects\working-dir-spheresfm\colmap\sparse-cubic-angled" -o "C:\Users\Admin\Pictures\Lichtfield\indoor-test-1\output_kgs_angled_100k" --strategy kgs --iter 100000 --enable-mip --progressive-resolution --mask-mode ignore --max-cap 2500000 --eval --train
pause
