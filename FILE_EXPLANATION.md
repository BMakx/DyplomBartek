# Dyplom.py - File Explanation

This document explains what `Dyplom.py` does, based on the implementation and the thesis PDF (`dwustronna inzynierka.pdf`).

## 1. Purpose of the script

`Dyplom.py` is a desktop GUI tool for statistical analysis of SEM images of nanostructures.

Main goal:
- automate repetitive SEM processing steps,
- reduce manual error,
- generate particle measurements, summary statistics, labeled images, and plots.

This matches the thesis objective: a repeatable SEM workflow using PyImageJ + Python data tools.

## 2. Technology stack

The script combines:
- **Tkinter**: GUI and user flow,
- **PyImageJ / ImageJ**: image preprocessing and particle analysis,
- **OpenCV**: manual scale-bar measurement UI,
- **Pandas / NumPy**: post-processing and statistics,
- **Matplotlib / Seaborn**: plot generation,
- **Pillow**: image preview and drawing particle labels.

## 3. End-to-end workflow

The user workflow in the app:
1. Select input SEM image.
2. Select output folder.
3. Set particle size filter (default `5000-Infinity` nm^2).
4. Optionally exclude edge-touching particles.
5. Click **Start**.
6. Manually measure scale bar on the image and enter its value in nm.
7. App runs full analysis and writes outputs.
8. App opens a result window with input/output images and summary statistics.

## 4. Processing pipeline implemented in code

The script pipeline closely follows the thesis chapter describing practical implementation:

1. **ROI crop**
- Keeps full width and top 92% of height.
- Removes the microscope text/metadata strip at the bottom.

2. **Contrast and conversion**
- Enhances contrast (`saturated=0.55`).
- Converts image to 8-bit grayscale.

3. **Segmentation**
- Applies automatic threshold (`Default dark`).
- Converts thresholded image to binary mask.
- Fills holes inside detected objects.

4. **Calibration**
- Uses user-measured scale bar distance in pixels + entered nm value.
- Sets measurement scale in ImageJ to nm.

5. **Particle analysis**
- Runs `Analyze Particles...` with user size filter and optional edge exclusion.
- Captures ImageJ results table and saves CSV.

6. **Derived metrics and statistics**
- Computes particle radius from area: `Radius = sqrt(Area / pi)`.
- Computes global statistics (mean/median/std for area, radius, roundness).
- Computes coverage (%) and particle density (particles per um^2).

7. **Reporting and visualization**
- Saves cleaned output image.
- Saves labeled output image with particle IDs at centroids.
- Exports statistics CSV.
- Exports main and additional plot sets.
- Shows final comparison and stat window in GUI.

## 5. Why manual scale measurement is used

The thesis describes an attempted automatic OpenCV scale-bar detection with limited robustness.
This script therefore uses an interactive/manual method:
- user clicks two points on the scale bar,
- app measures pixel distance,
- user enters real nm value.

This approach improves reliability across varying SEM image conditions.

## 6. Output files generated

For input file prefix `<name>`, the script writes:

- `<name>_wynik_csv.csv` - raw particle measurements (and radius added),
- `<name>_wynik_pixels.csv` - centroid coordinates converted to pixel space,
- `<name>_wynik_bez_etykiet.jpg` - processed output image without IDs,
- `<name>_wynik_jpg.jpg` - processed output image with particle IDs,
- `<name>_wyniki_stat.csv` - aggregated statistics,
- `<name>_wykresy.png` - main plot panel,
- `<name>_wykresy_dodatkowe.png` - additional plots.

## 7. Key strengths of current implementation

- Strong alignment with thesis objectives and described methods.
- Practical GUI for non-programmer lab users.
- Full pipeline from image to statistical report in one run.
- Clear outputs for both quantitative analysis and visual verification.

## 8. Known limitations / extension ideas

- Requires manual scale-bar interaction each run.
- Processing parameters (threshold mode, contrast saturation) are fixed in code.
- No batch mode for multiple images yet.
- Could be extended with parameter presets and automatic quality checks.

## 9. Summary

`Dyplom.py` is the core engineering implementation of the thesis: a lab-focused SEM analysis application that combines ImageJ processing with Python-based statistics and visualization, delivering repeatable and faster nanostructure characterization.
