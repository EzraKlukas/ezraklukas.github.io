---
layout: post
title: Real-time EMG-driven control framework
description: This post summarizes my current summer work in UBC Kinesiology's Sensorimotor Physiology Lab, building the embedded/software core for a real-time EMG-driven experimental control framework. The goal is to move from force-plate driven intervention toward low-latency motor-unit based control, while keeping the system modular enough that future experiments can be built on top of it.
skills:
  - Real-time PREEMPT_RT Linux development
  - C / C++
  - CMake
  - git
  - gdb
  - Eigen / BLAS
  - EtherCAT
  - IgH EtherCAT Master
  - CiA 402 servo control
  - FPGA development
  - SystemVerilog
  - Vivado / XSim
  - Oscilloscope and logic analyzer debugging
  - Signal processing
  - Linear algebra
  - Statistics
  - Blind source separation
  - ROS2 system design
  - Technical documentation and handoff
main-image: emg_decomp_diagram.png
---

# Control Problem Motivation

Broadly, the Sensorimotor Physiology Lab, where I am working this summer, studies the human balance control system. One natural way to study such a system is to perturb it, measure how it responds, and then ask what happens when we intentionally intervene in the loop.

This is where real-time control becomes interesting. For example, one might want to amplify or alter the response to vestibular input as a way of probing balance control, or eventually as a way of assisting people at higher fall risk. The lab already has real-time control loops which use state information and force-plate input to command a motorized experimental platform. The robot below is the current platform that this loop is implemented on, and part of the longer-term goal is to migrate toward the framework we are developing this summer.

![(currently) force plate driven robot]({{ page.url | remove: 'index/' | append: 'robot_photo.jpg' | relative_url }})

There are two practical limitations to using output force as the main input to a control loop. First, the force appears relatively late in the chain from brain intent to mechanical output. Different muscles and motor units also have different delays, so once the output is summed into force, a lot of the timing information we care about has already been blurred together. Second, for people whose neural commands do not translate cleanly into output force, force alone is not always the right place to look for intent.

The motivating idea is therefore to move the input of the control loop higher up the chain: from measured force, toward the electrical activity of the muscle, and eventually toward the discharge timings of individual motor units.

# EMG decomposition: the signal-processing problem

Muscle fibres are electrically stimulated to contract by motor neurons. One motor neuron and all the muscle fibres it controls form a **motor unit**, and each discharge from that motor neuron creates an electrical waveform called a **motor unit action potential** (MUAP). With high-density EMG, many electrodes record different mixtures of these same underlying motor unit events.

![EMG decomposition overview]({{ page.url | remove: 'index/' | append: 'emg_decomp_diagram.png' | relative_url }})

A useful way to model this is as a convolutive mixture. Each measured channel is the sum of several motor-unit spike trains, each filtered by the MUAP shape seen at that electrode:

$$
x_i(k) = \sum_{l=0}^{L-1}\sum_{j=1}^{n} h_{ij}(l)s_j(k-l) + n_i(k).
$$

Here, $x_i(k)$ is the EMG signal recorded on channel $i$, $s_j(k)$ is the spike train of motor unit $j$, $h_{ij}(l)$ is the MUAP shape from motor unit $j$ as seen on electrode $i$, and $n_i(k)$ is noise. This is a blind source separation problem: the sources are not directly visible, and the number and shape of the sources are not known ahead of time.

For the real-time control problem, the important distinction is between **offline decomposition** and **online projection**. Offline decomposition can be computationally heavier and is used to find motor-unit filters from an initial recording. Once those filters are known, online decomposition is much more direct: take the most recent multichannel EMG window, extend/demean it in the same way as the offline algorithm, project it through the trained filters, and classify local maxima as discharge events.

This is the core purpose of my C++ project, [emg-rt](https://github.com/EzraKlukas/emg-rt): make the online side deterministic, fast, and cleanly integrated with the rest of the experimental system.

# System architecture

At a high level, the system has three timing-critical jobs:

1. acquire EMG/IMU/ADC data with timestamps,
2. run online decomposition on the Jetson,
3. publish motor commands on a deterministic EtherCAT cycle.

The diagram below is not meant to imply that every feature is finished, but it gives the intended shape of the system. The Jetson runs the real-time compute and EtherCAT master. The Red Pitaya acts as the FPGA-facing acquisition system. A host computer is still useful for offline decomposition, visualization, parameter selection, and experiment orchestration.

![System architecture diagram]({{ page.url | remove: 'index/' | append: 'emg_rt_architecture.png' | relative_url }})

A major part of my work has been deciding where the real-time boundaries should be. ROS2 is very useful for orchestration, visualization, and experiment structure, but I do not want the hardest timing guarantees to depend on normal ROS2 message passing. The core loop is therefore designed around lower-level C++ data structures and real-time threads, with ROS2 sitting around the system rather than inside every deadline-critical path.

The C++ acquisition side has evolved quite a bit. Earlier designs centered around a single EMG ring buffer. The current design is closer to what the full acquisition system actually needs: an `AcquisitionFrameBuffer` owns parallel acquisition buffers for EMG, IMU, and ADC data, while each `AcquisitionRingBuffer` stores fixed-duration sensor history with timestamps and monotonically increasing sample indices. Readers own their own last-read index, which is important because the decomposition thread, logging thread, and visualization thread should not all be fighting over one shared `read_head`.

This is one of those design choices that looks like bookkeeping at first, but is really about making the system maintainable. Once several future students are adding new sensors, loggers, and analysis nodes, hidden ownership of buffer state becomes a great way to create subtle timing bugs.

# EtherCAT: deterministic motor command output

EtherCAT is the motor-output side of the system. In normal Ethernet, packets are routed as fairly independent messages. EtherCAT is different: a frame passes through the slave devices in a deterministic order, and each device reads or writes its process data as the frame passes through. For a real-time motor loop, this is exactly the kind of structure we want. The master can assemble command data, exchange process data with the slaves, and synchronize the timing of outputs through distributed clocks.

In practice, my work here involved bringing a Teknic ClearPath EtherCAT servo through the CiA 402 state machine, mapping the relevant PDOs, and running cyclic synchronous position commands from the Jetson. I started with SOEM, evaluated Acontis, and eventually moved toward IgH EtherCAT Master with an Intel i210 NIC using the `ec_igb` driver. The point of that hardware/software choice was not just to make the motor move; it was to make the timing measurable and bounded enough that the rest of the real-time loop could be designed with actual margins.

A useful way to think about the cycle is:

1. the master thread wakes up at the start of the period,
2. it receives and processes the previous process-data frame,
3. it reads servo state and writes the next target command,
4. it queues and sends the next EtherCAT frame,
5. the servo applies the output at the synchronized hardware time.

The two most important timing measurements were wake-up latency and execution time. Wake-up latency tells me how late the real-time thread started relative to the requested time. Execution time tells me how long the EtherCAT receive/process/write/send sequence took once the thread was awake. The sum of those two gives the deadline usage.

At 1 kHz, the IgH/i210 setup gave very encouraging margins:

| Test condition | Worst latency | Worst execution | Worst deadline usage | Remaining 1 ms margin |
| --- | ---: | ---: | ---: | ---: |
| 10 min, no stress | 24.0 µs | 31.8 µs | 42.4 µs | 957.6 µs |
| 10 min, CPU + memory + I/O stress | 62.9 µs | 80.6 µs | 96.6 µs | 903.4 µs |
| 1 hour, maximum stress | 97.2 µs | 97.7 µs | 118.8 µs | 881.2 µs |

![Worst per-second EtherCAT deadline usage over one hour at maximum stress]({{ page.url | remove: 'index/' | append: 'ethercat_deadline_usage_one_hour.png' | relative_url }})

These numbers were a big turning point for me. They made the EtherCAT side feel less like a black box and more like a well-characterized piece of the larger timing budget. A 2 kHz loop also appears plausible, though I would want more careful testing before treating it as the main design point. For now, 1 kHz gives a comfortable baseline while leaving substantial time for EMG decomposition and command generation.

# Real-time decomposition performance

The other half of the timing question is whether online EMG decomposition can run quickly enough on the Jetson. I started with a straightforward C++ implementation, then added profiling around each major stage: writing into the acquisition buffer, reading into the grid workspace, extending the signal, demeaning, projecting through the MU filters, finding local maxima, and thresholding discharges.

The first version was much slower than it needed to be, especially in the pulse-train projection step. Rewriting the hot loop around Eigen matrix operations made a large difference. Another important lesson came from profiling strange 50 ms latency spikes: they were not algorithmic at all, but came from Linux real-time throttling. Disabling RT bandwidth enforcement for this dedicated real-time setup removed those periodic stalls.

In one representative offline replay on the Jetson, after CPU isolation and real-time scheduling changes, the decomposition path was no longer the bottleneck:

| Section | Mean | Worst observed |
| --- | ---: | ---: |
| Full cycle | 10.7 µs | 55.3 µs |
| EMG decomposition | 9.7 µs | 24.0 µs |
| Pulse-train projection | 5.2 µs | 40.9 µs |
| Ring-buffer sample read | 0.087 µs | 9.2 µs |

I do not want to overstate this as the final end-to-end result, because replaying stored data is not the same as closing the loop with live acquisition. Still, it is a very encouraging result. It suggests that the C++ decomposition computation itself is fast enough that the remaining hard problems are mostly system integration, acquisition timing, and validating that the detected motor units are physiologically meaningful.

![Example spike-triggered average from FastICA decomposition work]({{ page.url | remove: 'index/' | append: 'fastica_muap_example.png' | relative_url }})

# Acquisition and FPGA work

The acquisition side has been the main place where the project became more hardware-facing than expected.

The Intan RHD2164 chip is attractive because it gives us 64 channels of amplified EMG data in a small front-end. The catch is that it uses a custom double-data-rate SPI interface: data is effectively transferred on both clock edges, which normal Jetson SPI drivers do not support. At the sampling rates we care about, bit-banging this reliably on Linux GPIO is not the right tool.

![Standard SPI compared with DDR SPI timing]({{ page.url | remove: 'index/' | append: 'sdr_vs_ddr_spi_timing.png' | relative_url }})

This is why the Red Pitaya FPGA exists in the system. The FPGA can do the timing-sensitive acquisition work close to the pins: DDR SPI, timestamping, synchronization, buffering, and transfer into the processor side. From there, packets can be sent to the Jetson over Ethernet. I do not want TCP itself to be the timing source; the timestamped samples and a deliberately delayed acquisition buffer are what let the Jetson consume data at a consistent offset from acquisition time.

Most of the surrounding FPGA acquisition system is now in place: the Red Pitaya-side buffering/transfer architecture, the DMA-facing path, packetization, and the Jetson-side acquisition-buffer design are largely established. The major missing hardware block is the Intan DDR SPI reader itself. That is the next piece I need to develop and validate carefully with simulation, scope/logic-analyzer traces, and eventually real Intan data.

# What I have learned so far

The biggest technical lesson has been that “real-time” is not the same as “fast.” Fast average performance is nice, but the quantity that matters for a control loop is the worst case. A 10 µs average with a hidden 50 ms stall is not a real-time loop; it is a demo that happens to work until it does not.

The second lesson is that interfaces matter as much as algorithms. A good motor-unit decomposition algorithm is only useful in a closed-loop experiment if the data arriving to it has bounded timing, clear ownership, and enough metadata to be trusted. This is why I have spent so much time on buffer ownership, timestamps, sample indices, profiling, and tests, even though those pieces are less glamorous than the signal processing itself.

The last lesson is more personal. I have been learning when to use AI as an accelerator and when to slow down and build understanding myself. It is very useful for boilerplate, testing prompts, and sanity-checking designs, but it is not a substitute for actually understanding why an EtherCAT cycle missed its timing, why an Eigen expression did the wrong broadcast, or why a sensor interface cannot be handled by a default driver.

# What still needs to be done?

There are three major next steps.

First, the Intan DDR SPI reader needs to be finished on the FPGA and validated from the pins upward. This is the main remaining acquisition block before we can retire the USB-facing Intan path for live real-time experiments.

Second, we need cleaner synchronized EMG/force trials to validate the force-mapping side. The software can already be tested with fake EMG and synthetic force mappings, but the biologically interesting part is learning a mapping from detected motor-unit discharge times to force output.

Third, the full loop needs to be closed in stages: fake EMG into EtherCAT commands, recorded EMG replay into EtherCAT commands, then live FPGA-acquired EMG into EtherCAT commands. Around that, ROS2 can provide experiment orchestration, logging, visualization, and higher-level UI tools without sitting directly inside the most timing-critical path.

If you've made it this far, thank you for reading. I hope this gives a useful picture of what my work has looked like so far: a mix of signal processing, real-time Linux, EtherCAT motor control, FPGA acquisition design, and a lot of careful debugging at the boundaries between them.
