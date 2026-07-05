---
layout: post
title: Robot Summer 2025 (ENPH 253)
description: >-
Each summer, sixty second year UBC engineering physics students get the privilege to bunker down in a specialized workshop 
custom built for the summer. The goal is, from scratch, to design, prototype, and build a fully autonomous robot to traverse a challengi
ng course, detect and pick up magnet-inserted stuffed pets, and return them to a home zone.
skills:
  - CAD, waterjet, laserjet, 3D printing
  - Handtool and machine prototyping
  - Breadboard circuit design and troubleshooting
  - KiCAD Schematic and PCB design
  - ESP32 microcontroller
  - Finite State Machine design
  - git, PlatformIO, C++
  - Datasheet traversal for IC use in circuit design
  - Oscilloscopes for debugging electromechanical systems
main-image: side_angle.webp
---

# Robot Summer 2025

This post is still intentionally a placeholder. I'll write out the full project page in more detail later, including the mechanical design, electrical systems, firmware architecture, debugging process, and competition strategy. For now, I wanted to at least include a quick visual snapshot of the robot and one of the sequences that captures the kind of integration work that went into the project.

![Robot with Shreya]({{ page.url | remove: 'index/' | append: 'robot_w_shreya.webp' | relative_url }})

## Calibration sequence

One of the important pieces of the robot was its startup calibration sequence. Before a run, the robot needed to put its actuators and sensing assumptions into a known state, rather than relying on everything being physically aligned by hand. This kind of sequence is not the most glamorous part of a robot, but it makes the system much more repeatable: when the run begins, the software can reason from a known configuration instead of from whatever slightly different state the robot happened to be left in.

<div class="video-container">
  <video class="post-video" controls preload="metadata" playsinline>
    <source src="{{ page.url | remove: 'index/' | append: 'calibration_sequence.mov' | relative_url }}" type="video/quicktime">
    Your browser does not support the video tag. You can still view the calibration sequence from the project directory.
  </video>
</div>

The full writeup will come later, so I do not want to over-explain the mechanism here without also giving the surrounding design context. The short version is that this is an example of the robot doing the kind of automatic setup that makes the rest of the autonomous behaviour less fragile: initialize, move through a known sequence, and only then trust the finite-state logic used during the competition run.
