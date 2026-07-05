---
layout: post
title: Robot Summer 2025 (ENPH 253)
description: >-
  Each summer, sixty second year UBC engineering physics students get the privilege
  to bunker down in a specialized workshop custom built for the summer. The goal
  is, from scratch, to design, prototype, and build a fully autonomous robot to
  traverse a challenging course, detect and pick up magnet-inserted stuffed pets,
  and return them to a home zone.
skills:
  - CAD, waterjet, laserjet, 3D printing
  - Handtool and machine prototyping
  - Breadboard circuit design and troubleshooting
  - KiCAD schematic and PCB design
  - ESP32 microcontroller
  - Finite state machine design
  - git, PlatformIO, C++
  - Datasheet traversal for IC use in circuit design
  - Oscilloscopes for debugging electromechanical systems
main-image: side_angle.webp
---

# Robot Summer 2025

This post is intentionally incomplete for now. I will write the full project page later with more detail on the mechanical design, electrical system, firmware architecture, debugging process, and competition strategy.

![Robot with Shreya]({{ page.url | remove: 'index/' | append: 'robot_w_shreya.webp' | relative_url }})

## Calibration sequence

Startup calibration matters because the robot needs to begin a run from a known mechanical and sensing state. A short repeatable sequence reduces dependence on hand alignment and makes the autonomous finite-state logic less fragile.

<div class="video-container">
  <video class="post-video" controls preload="metadata" playsinline>
    <source src="{{ page.url | remove: 'index/' | append: 'calibration_sequence.mov' | relative_url }}" type="video/quicktime">
    Your browser does not support the video tag.
  </video>
</div>
