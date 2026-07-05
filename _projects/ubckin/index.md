---
layout: post
title: Real-time EMG-driven control framework
description: This post shows a bit of the work I've been up to at my current summer internship at the Sensorimotor and Physiology lab, working under Dr. Sebastien Blouin, and alongside a few other talented engineering undergrads. This control framework aims to considerably cut the delay between human intent of motion and intervened output, which will offer many novel methods and models for the human control system to be researched. The system is also designed to be the core for a ROS2-orchestrated versatile experimental platform, offering researchers with little to no embedded / software understanding to design and run experiments, similar to what LabView can offer. The system is designed to be hard real-time, with core processing running on an NVIDIA Jetson Orin Nano with PREEMPT_RT patch and kernel modifications. EMG and IMU acquisition is mastered by a Red Pitaya FPGA development board, and ADC acquisition and motor control is mastered by an EtherCAT kernel module on the Jetson.
skills: 
  - Real-time PREEMPT_RT linux development
  - C / C++
  - CMake
  - git 
  - gdb 
  - Eigen / BLAS
  - EtherCAT
  - FPGA Development: SystemVerilog, Vivado, XSim, Oscilloscope, Logic analyzer
  - Signal processing
  - linear algebra 
  - statistics
  - Blind Source Separation problem
  - ROS2
  - Communication, effectively working with peers

main-image: emg_decomp_diagram.png
---
# Control Problem Motivation
Broadly, the Sensorimotor and Physiology lab, where I am working this summer, seeks to study the human balance control system. Sensibly, one of the main ways to study such a system is to investigate its response to external stimuli. Upon constructing a model for a control mechanism, it's also helpful to study what happens when we intentionally intervene with the actual mechanism. This is where the need for realtime control presents itself. For example, one might be interested in the effect of amplifying the amplitude response to vestibular inputs as a means of helping individuals at higher fall-risk. So far, we've implemented real-time control loops that take state data and force plate input and calculate appropriate motor command outputs in an experiment. See the robot that this loop is currently implemented, and on which we aim to migrate to the framework we're developing this summer.

![(currently) force plate driven robot]({{ page.url | remove: 'index/' | append: 'robot_photo.jpg' | relative_url }})

There are at least two practical limitations to using outputted force as an input to a control loop:
1. The latency between when the brain (the heart of the human control system) produces its intended command and when that output appears is quite substantial (up to 100 ms), and variable between muscle types (slow twitch vs. fast twitch). The variability of latency across different muscle-types that might contribute to a force output makes it impossible to understand to retrieve a more fine-grained view of the brain's intent.
2. For individuals who's brain commands don't properly translate to an output force, it's impossible to interpret intended force.

Among others, these reasons justify the need for the control loop input to be higher up the brain -> output force command chain than what we currently have capability for. Thankfully, with the accessibility of higher-power compute, good quality electromyography sensors and amplifiers, and cheap student labour, we can aspire to use the electrical signals from individual motor neuron impulses as the input to our control loop.

# EMG decomposition: a context

Muscles fibres are electrically stimulated to contract by specialized motor neurons. A motor neuron can control anywhere from a few to thousands of muscle fibres. A motor neuron and all its associated controlled muscle fibres makes up one **motor unit**, and a motor neuron causes contraction by periodically firing electrical discharge signals, whose shape we can detect as a **motor unit action potential (MUAP)**. Several main EMG measuring techniques are of relevance to the lab: high density surface arrays (HDsEMG), and indwelling threaded myomatrix arrays. So far we have worked more with HDsEMG, but the firmware thankfully translates, as both methods use grids that interface with the same [RHD 2164 chip](https://intantech.com/files/Intan_RHD2164_datasheet.pdf), which amplifies and serializes 64-channel EMG signal. Because motor units are localized and signals don't propagate instantaneously or even linearly, their strength and phase varies between electrodes. It's important to note that signals propagate enough in multi-channel recordings that several (often up to all) electrodes in a grid receive signal contributions from all local motor units. Hence, measured signals can be described as a convolutive mixture of a series of delta functions, representing the discharge timings of the motor units [Negro et al. 2016](https://pubmed.ncbi.nlm.nih.gov/26924829/), whose finite duration impulse responses are the MUAP's:

$$ x_i(k) = \sum_{l=0}^{L-1}\sum_{j=1}^{n} h_{ij}(l)s_j(k-l) + n_{i}(k), $$

where $x_i(k)$ is the i'th EMG channel at sample point $k$, $h_{ij}(l)$ is the action potential of the $j$th motor unit as recorded from electrode $i$, and $s_j(k)$ is the spike train (discrete superposition of unit spike functions) of the $j$th motor unit, and $n_{i}(k)$ is the additive noise at electrode $i$, and $L$ is the duration of the action potential impulse response.
This model sets the stage for Blind Source Separation (BSS) algorithms, such as the famous cocktail party problem: how can you isolate a single voice from a complex mix of background noise and conversations? It is 'blind' in the sense that we don't know how many motor units (whose MUAP convoluted spike trains are analagous to voices) there are, nor do we know anything specific about them. There's lots to be said about how to solve such a problem, but I'll dedicate another page for that (for now, see this delightful tutorial written by the founder of FastICA, one of the algorithms I've implemented: [ICA: a tutorial](https://www.cs.jhu.edu/~ayuille1/courses/Stat161-261-Spring14/HyvO00-icatut.pdf)).

While lots can be said simply from the RMS amplitude of an EMG signal, there are several reasons to want to recover individual MU discharge times. For one, RMS amplitude corrupts as an identifier of output force when muscles become tired. Next, RMS can say nothing about the individual degrees of freedom which contributing MU's add (what if we want to determine which finger contracted). Also, MU's can have a vast range of delays between discharge timing and correspondent force output; this is the fundamental difference between fast-twitch and slow-twich muscles, and lacking foreknowledge of intended delay between EMG contribution and force output makes the problem of force reconstruction undefined. Motivated to understand the brain's control system, fine-grained insight to the activation of different types of MU's offers both greater insight to balance mechanisms, and enables us to superpose force outputs using a model that is truer to how humans generate force.

As hinted above, several methods of EMG decomposition exist, but real-time decomposition into motor unit spike-trains is currently only possible once initial offline decomposition has been run. Given an initial EMG recording in a session, offline decomposition entails iteratively finding appropriate 'MU filters' who, when projected onto multi-channel, temporally extended EMG signal, yields a MU's spike-train, indicating discharge times of a motor unit (soon I'll include a figure illustrating the signal processing steps). The MU filters are found offline, and the projection to generate spike-trains occurs online. Even though many different offline decomposition algorithms exist, by some clever algorithms their output can always be translated to the same format of multi-channel MU filters who can be projected to generate MU spike-trains in real-time.

Currently, the core purpose of [emg-rt](https://github.com/EzraKlukas/emg-rt) is deterministic us-level latent high-frequency (up to 4 kHz) signal acquisition, and real-time MU filter projection. The key output is discharge_times, which will be convoluted with pre-calculated MU-specific force impulse responses (this is where transfer functions can be skewed for research purposes) and translated to appropriate servo motor control commands. While other real-time decomposition implementations exist, none are designed with high-frequency or real-time control in mind.

# Real-time EMG signal acquisition

A challenge with designing hard real-time (meaning failure to meet a deadline is treated as catastrophic) loops is that every element of the system must have a sufficiently low bounded latency. For example, this is why many nodes in the ROS2 system don't primarily communicate via ROS2 DDS communication protocol. As another example, acquiring EMG data at a deterministic rate with bounded jitter. The current EMG acquisition module uses the USB 3.0 SS hardware and protocol, which is designed for maximal throughput, not determinism. This makes bounding data-transfer latency unrealistic. Inconsistent bounds on data acquisition time means no guarantee can be made that an output command could be supplied within some $\Delta t$ of input acquisition time.

Thankfully, the Intan RHD2164 chip itself communicates with SPI. Unfortunately, to accomodate up to 30 kHz 64-channel sampling rates, Intan implements a custom double data rate (DDR) SPI protocol, which default FPGA and NVIDIA Jetson SPI drivers don't accomodate. As such, the only way accomodate low jitter real-time EMG data acquisition with the Intan chips is to implement an SPI DDR master on an FPGA, and send FPGA time-stamped and packeted data to the NVIDIA Jetson (where decomposition runs) with a more deterministic transfer method; we've chosen TCP for its safety and low overhead. The FPGA acquisition system is the topic of another page, as we've also used FPGA as the translation layer for IMU's and a few ADC's.

# Lessons Learned
There are too many to name, but one big detour we've taken that should have been addressed earlier is due to the fact that Intan's EMG sensors don't use an SPI protocol that typical default drivers accomodate. I didn't scower the data-sheet when making the assumption that the NVIDIA Jetson could acquire directly from the sensors, which changed acquiring EMG data on the Jetson from being a few hour project to taking several weeks of learning FPGA development and implementing and testing my own module. I'm ultimately thankful for the deep FPGA waters it's exposed me to, but I obviously want to work as efficiently and quickly as possible.

Another set of lessons I'm learning is about when it's worth giving a problem to AI, and when it's worth doing yourself. It's a fast-changing landscape of defining what problems are brainless and which aren't, and learning the balance between when to trust AI with an easily definable boring coding task, versus when I place greater value on learning a skill from the bottom up without wasting my employer's time has been an often confusing journey. That said, learning this balance has also been deeply rewarding, because I've become far more efficient while still learning lots of skills and deep understanding that many peers might not be able to boast because of relying on AI with too much, too early.

Lastly, regarding working well and taking initiative in teams, initiating low-stakes check-ins has always been fruitful in so many ways. For one, it builds safety and trust within the team, and has often led to offering a listening ear that someone has needed to quickly come to a problem's solution. Selfishly for me though, it both helps both of us find and clear misunderstandings about tasks we're working on together, as well as give me a deeper understanding of their work, reducing the barrier of entry both to helping, and for me to learn a skill or system I wouldn't otherwise have learned.

# What still needs to be done?
For one, the control loop still needs to be closed. The main road-block at the moment is designing and acquiring the mapping from discharge time to output force. We attempted a trial to gather EMG and force synchronized data to begin developing, but in light of a recent move and related troubles, a faulty synchronization signal generation and some noisy EMG channels halted success. Even so, we will generate a fake convolutive mapping so that the software and hardware framework can be tested with fake EMG data translating to EtherCAT commands.

As well, the ROS2 abstraction experiment manager and all related UI features are still in development. The goal would be for a UI interface similar to LabView to permit researchers to essentially drag and drop, and run functions that use chosen real-time acquired inputs, and translate to chosen output controls. These functions will be encapsulated with ROS2 nodes for experiment-time visibility, and distinction will be made between when to use ROS2 intranode communication, or lower level, low latency on-Jetson communication for control. The advantage is that several machines (such as a VR headset, for example) can be managed on one ROS2 network, providing visibility, debugging capabilities, and live host computer visualization during an experiment.

We also want to provide the opportunity to add more DAC or digital I/O EtherCAT terminal slaves to the network, so further modificiation can be made to what data is being acquired in an experiment. For this feature I still need to adapt the EtherCAT motor specific Jetson master to detect and handle communication with theoretically any number of slaves, and make relevant data transparent and accessible to ROS2 nodes via ROS2 DDS (at the tradeoff of increased latency / jitter) or at a lower level. 

Lastly, but very importantly, the FPGA DDR SPI module for EMG acquisition is not yet complete, and we've been using Intan's USB-facing EMG acquisition module so far. However, the surrounding architecture of DMA, buffering, packetizing, and TCP communication from Pitaya to Jetson is ready, so FPGA development is near the finish line.

If you've made it this far, thank you for reading. I hope this has given you a helpful look into what I've been working on this summer, and would love to chat if you have any questions!

Ezra
