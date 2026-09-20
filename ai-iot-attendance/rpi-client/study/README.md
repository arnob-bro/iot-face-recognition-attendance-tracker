# Raspberry Pi Heat Test Study

This folder contains the evidence and analysis used to evaluate whether the Raspberry Pi can run the attendance workload reliably under thermal stress.

## Why this study matters

For a final submission, this study is important because it moves the project from “it works in theory” to “it remains stable under real operating conditions.” The heat test helps answer a practical engineering question:

- Can the Raspberry Pi maintain the attendance workload without overheating or throttling?

This is especially relevant because the project includes camera-based recognition, multiple processes, and long-running execution. If the device overheats, the system may slow down or fail during attendance capture.

## Study objective

The goal is to measure and document the Pi’s thermal and performance behavior during a realistic attendance workload.

The study records:

- CPU temperature
- CPU utilization
- memory usage
- number of attendance processes
- throttling status
- elapsed time

These values show whether the device stays within a safe operating range or whether thermal throttling begins to degrade system performance.

## Files in this folder

- `analyze_heat_test.py` — reads a CSV and prints a readable summary of the experiment
- `visualize_heat_test.py` — creates a visual chart from the CSV for interpretation
- `heat_test_plot.png` — sample chart generated from the included dataset
- `../heat-test.csv` — raw captured data from a Raspberry Pi heat test

## Recommended workflow for a final submission

### 1. Run the heat test on the actual device

Use the real Raspberry Pi hardware running the attendance client. Keep the workload representative of normal use, including camera access and recognition.

```bash
cd /home/pi/ai-iot-attendance/rpi-client
python tools/heat_test.py --output logs/heat-test.csv --interval 5 --duration 7200
```

This creates a structured dataset that can be used as evidence in the report.

### 2. Analyze the raw data

```bash
cd /home/pi/ai-iot-attendance/rpi-client
python study/analyze_heat_test.py heat-test.csv
```

This gives a concise summary including:

- average and maximum temperature
- average and maximum CPU usage
- memory usage
- number of throttling events
- attendance-process count

### 3. Generate the visual summary

```bash
cd /home/pi/ai-iot-attendance/rpi-client
python study/visualize_heat_test.py heat-test.csv --output study/heat_test_plot.png
```

This creates a clear chart that makes the thermal behavior easy to explain in a report or presentation.

### 4. Interpret the results

Look for the following:

- temperature rising steadily over time
- peaks close to or above 80C
- repeated throttling events
- CPU saturation near 100%
- more than one attendance process running at the same time
- slower or unstable recognition during the test

## What counts as a good result

A strong result for a final project is:

- temperature remains stable over time
- no significant throttling is detected
- the system keeps processing the recognition workload without instability
- the generated chart shows a controlled thermal pattern

## What counts as a problem

A weak result is:

- repeated temperature spikes
- thermal throttling appears in the dataset
- the Pi begins to lag during recognition
- the attendance process count becomes abnormal or unstable

These outcomes should be highlighted honestly in the report because they show real-world performance constraints.

## Final-submission presentation format

To make the study stronger for evaluation, include the following in your report:

1. Objective
   - State that the study measured thermal stability during live attendance processing.

2. Method
   - Explain the heat-test setup and sampling interval.
   - Mention the duration and the workload conditions.

3. Results
   - Report average/max temperature, CPU, and memory.
   - Mention whether throttling occurred.

4. Visualization
   - Include the generated plot as evidence.

5. Discussion
   - Explain whether the system remained stable or started to degrade under load.
   - Connect the result to camera recognition performance and system reliability.

6. Conclusion
   - State whether the Pi is suitable for the use case or whether improvements are needed.

## Example final-report statement

> The Raspberry Pi heat test was conducted over a 2-hour workload period while the attendance application ran in normal operating mode. The recorded data showed stable temperature behavior with no thermal throttling events, indicating that the device remained within acceptable operational limits during the test period. The visual chart confirms that the system maintained steady thermal performance without evidence of overheating.

## Suggested evidence to include

For final submission, include:

- the raw CSV file
- the summary output from the analyzer
- the generated plot image
- a short paragraph explaining the trend and its significance

This combination makes the study look like proper engineering evidence rather than only a technical experiment.

## Recommended next step

If the goal is to improve the study for grading, the most useful enhancement is to add a short results section to the project report that references the CSV, the summary output, and the plotted chart together. That makes the evidence clear, credible, and easy for reviewers to evaluate.
